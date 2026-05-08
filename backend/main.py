"""FastAPI backend for MySQL DBRE Agent chat interface."""

import json
import logging
import os

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import ollama

from backend.schemas import ChatRequest
from config import MySQLConfig
from database import MySQLDBREConnection, MySQLMetricsCollector

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="MySQL DBRE Agent API", description="Chat API for MySQL database reliability engineering")

# CORS configuration for localhost development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
db_connection = None
metrics_collector = None
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:latest")
OLLAMA_TEMPERATURE = float(os.getenv("OLLAMA_TEMPERATURE", "0.1"))


def init_clients():
    """Initialize database clients."""
    global db_connection, metrics_collector

    config = MySQLConfig.from_env()
    db_connection = MySQLDBREConnection(config)
    db_connection.connect()
    metrics_collector = MySQLMetricsCollector(db_connection)

    logger.info("Clients initialized successfully")
    logger.info(f"Using Ollama model: {OLLAMA_MODEL}")


def execute_tool(tool_name: str, tool_input: dict) -> str:
    """Execute a MySQL tool and return the result as a JSON string."""
    try:
        if tool_name == "mysql_get_uptime":
            result = metrics_collector.get_uptime()
        elif tool_name == "mysql_get_thread_stats":
            result = metrics_collector.get_thread_stats()
        elif tool_name == "mysql_get_qps":
            result = metrics_collector.get_qps_stats()
        elif tool_name == "mysql_get_replication_status":
            result = metrics_collector.get_replication_status()
        elif tool_name == "mysql_get_node_type":
            result = metrics_collector.get_node_type()
        elif tool_name == "mysql_get_replication_topology":
            result = metrics_collector.get_replication_topology()
        elif tool_name == "mysql_get_processlist":
            limit = tool_input.get("limit", 50)
            result = metrics_collector.get_processlist(limit=limit)
        elif tool_name == "mysql_get_slow_queries":
            result = metrics_collector.get_slow_queries()
        elif tool_name == "mysql_execute_safe_query":
            query_name = tool_input.get("query_name")
            result = db_connection.execute_safe_query(query_name=query_name)
        elif tool_name == "mysql_ask_question":
            question = tool_input.get("question")
            result = {"answer": f"Natural language question: {question}"}
        else:
            result = {"error": f"Unknown tool: {tool_name}"}

        return json.dumps(result)
    except Exception as e:
        logger.error(f"Error executing tool {tool_name}: {str(e)}")
        return json.dumps({"error": str(e)})


async def stream_chat_response(user_message: str, history: list = None):
    """Stream chat response using Ollama with tool execution."""
    try:
        if history is None:
            history = []

        # Build conversation history (support Pydantic objects or plain dicts)
        messages = []
        for msg in history:
            role = getattr(msg, "role", None) or (msg.get("role") if isinstance(msg, dict) else "user")
            content = getattr(msg, "content", None) or (msg.get("content") if isinstance(msg, dict) else "")
            messages.append({"role": role, "content": content})

        # Add new user message
        messages.append({"role": "user", "content": user_message})

        # System prompt with tool descriptions and instructions.
        system_prompt = """You are a MySQL Database Reliability Engineering (DBRE) expert assistant.
Your role is to help users monitor and understand their MySQL database health and performance.

VERIFICATION RULES (must follow exactly):
1) Always cite the exact tool output you used (include the raw field names/values).
2) For numeric conversions (time, rates), prefer server-verified values and explicit calculations returned by the backend.
3) If a user reports an error, acknowledge and apologize briefly, explain the mistake, show the corrected computation using server-verified values, and provide a short plan to avoid similar mistakes.

Use ONLY the following whitelisted tools:
- mysql_get_uptime
- mysql_get_thread_stats
- mysql_get_qps
- mysql_get_replication_status
- mysql_get_node_type
- mysql_get_replication_topology
- mysql_get_processlist
- mysql_get_slow_queries
- mysql_execute_safe_query

Format tool calls exactly as: [TOOL: tool_name param=value]
"""

        # Prepare messages for Ollama (prepend the system prompt into the first user message)
        messages_for_ollama = []
        system_msg_added = False
        for msg in messages:
            if not system_msg_added and msg.get("role") == "user":
                messages_for_ollama.append({
                    "role": "user",
                    "content": f"{system_prompt}\n\nUser query: {msg['content']}"
                })
                system_msg_added = True
            else:
                messages_for_ollama.append(msg)

        # Get initial response to determine tool usage
        initial_response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=messages_for_ollama,
            stream=False,
        )

        initial_text = initial_response.get("message", {}).get("content", "")
        logger.info(f"LLM suggested response: {initial_text[:200]}...")

        # Parse tool calls from the response
        tool_calls = []
        for line in initial_text.splitlines():
            if "[TOOL:" in line:
                start = line.find("[TOOL:") + 6
                end = line.find("]", start)
                if end > start:
                    tool_call = line[start:end].strip()
                    tool_calls.append(tool_call)

        # Execute identified tools
        tool_results = {}
        if tool_calls:
            logger.info(f"Executing {len(tool_calls)} tools: {tool_calls}")
            for tool_call in tool_calls:
                parts = tool_call.split()
                tool_name = parts[0]
                tool_params = {}
                for part in parts[1:]:
                    if "=" in part:
                        k, v = part.split("=", 1)
                        try:
                            tool_params[k] = int(v)
                        except ValueError:
                            tool_params[k] = v

                logger.info(f"Executing tool: {tool_name} with params: {tool_params}")
                result_json = execute_tool(tool_name, tool_params)
                try:
                    tool_results[tool_name] = json.loads(result_json)
                except Exception:
                    tool_results[tool_name] = {"error": "Failed to parse tool result"}

            # Notify client tools executed
            yield f"data: {json.dumps({'type': 'tool_execution', 'tools': list(tool_results.keys())})}\n\n"

            # Synthesize final answer using tool results
            tools_summary = json.dumps(tool_results, indent=2)
            synthesis_messages = messages_for_ollama + [
                {"role": "assistant", "content": initial_text},
                {"role": "user", "content": f"Here are the actual database query results:\n\n{tools_summary}\n\nPlease provide a concise answer using the real data."}
            ]

            final_response = ollama.chat(
                model=OLLAMA_MODEL,
                messages=synthesis_messages,
                stream=False,
            )

            response_text = final_response.get("message", {}).get("content", "")
        else:
            logger.info("No tools identified in response, using initial response")
            response_text = initial_text

        yield f"data: {json.dumps({'type': 'text', 'content': response_text})}\n\n"

    except Exception as e:
        logger.error(f"Error in stream_chat_response: {str(e)}", exc_info=True)
        yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"


@app.on_event("startup")
async def startup_event():
    """Initialize clients on startup."""
    try:
        init_clients()
    except Exception as e:
        logger.error(f"Failed to initialize clients: {str(e)}")
        raise


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}


@app.post("/api/chat")
async def chat(request: ChatRequest):
    """Chat endpoint for sending messages and receiving responses."""
    try:
        if not db_connection or not db_connection.is_connected():
            raise HTTPException(status_code=503, detail="Database connection not available")

        return StreamingResponse(
            stream_chat_response(request.message, request.history),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
