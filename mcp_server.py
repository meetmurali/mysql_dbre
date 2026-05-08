"""MCP Server for MySQL DBRE Agent.

This exposes the MySQL DBRE Agent as an MCP server that Claude Code can use.
"""

import asyncio
import json
import os
from typing import Any

from dotenv import load_dotenv
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel,
)
import mcp.types as types

from agent import MySQLDBREAgent
from config import MySQLConfig
from database import QueryNotAllowedError, MySQLConnectionError

load_dotenv()

# Global agent instance
_agent: MySQLDBREAgent | None = None


def get_agent() -> MySQLDBREAgent:
    """Get or create the MySQL agent."""
    global _agent
    if _agent is None:
        db_config = MySQLConfig.from_env()
        _agent = MySQLDBREAgent(db_config=db_config)
        _agent.connect()
    return _agent


# Create the MCP server
app = Server("mysql-dbre-agent")


@app.list_resources()
async def list_resources() -> list[Resource]:
    """List available MySQL resources."""
    return [
        Resource(
            uri="mysql://status/uptime",
            name="MySQL Uptime",
            description="Server uptime in seconds",
            mimeType="application/json",
        ),
        Resource(
            uri="mysql://status/threads",
            name="MySQL Threads",
            description="Current thread statistics",
            mimeType="application/json",
        ),
        Resource(
            uri="mysql://status/replication",
            name="MySQL Replication Status",
            description="Replication lag and status",
            mimeType="application/json",
        ),
        Resource(
            uri="mysql://status/node",
            name="MySQL Node Type",
            description="Whether this is Primary or Replica",
            mimeType="application/json",
        ),
        Resource(
            uri="mysql://status/topology",
            name="MySQL Replication Topology",
            description="Replication topology information",
            mimeType="application/json",
        ),
        Resource(
            uri="mysql://metrics/qps",
            name="MySQL QPS",
            description="Queries per second metrics",
            mimeType="application/json",
        ),
    ]


@app.read_resource()
async def read_resource(uri: str) -> str:
    """Read a MySQL resource by URI."""
    agent = get_agent()

    resource_map = {
        "mysql://status/uptime": lambda: agent.metrics.get_uptime(),
        "mysql://status/threads": lambda: agent.metrics.get_thread_stats(),
        "mysql://status/replication": lambda: agent.metrics.get_replication_status(),
        "mysql://status/node": lambda: agent.metrics.get_node_type(),
        "mysql://status/topology": lambda: agent.metrics.get_replication_topology(),
        "mysql://metrics/qps": lambda: agent.metrics.get_qps_stats(),
    }

    if uri not in resource_map:
        raise ValueError(f"Unknown resource: {uri}")

    try:
        data = resource_map[uri]()
        return json.dumps(data, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools for the MySQL DBRE Agent."""
    return [
        Tool(
            name="mysql_get_uptime",
            description="Get MySQL server uptime in seconds and human-readable format",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="mysql_get_thread_stats",
            description="Get current MySQL thread statistics including running threads, connections, and max connections",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="mysql_get_qps",
            description="Get MySQL queries per second (QPS) statistics",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="mysql_get_replication_status",
            description="Get MySQL replication status including lag, IO/SQL thread status, and source host information",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="mysql_get_node_type",
            description="Determine if this MySQL node is a Primary (master) or Replica (slave) node",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="mysql_get_replication_topology",
            description="Get MySQL replication topology including server ID, connected replicas, and node relationships",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="mysql_get_processlist",
            description="Get current MySQL process list showing active queries and connections",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of processes to return (default: 50)",
                    }
                },
                "required": [],
            },
        ),
        Tool(
            name="mysql_get_slow_queries",
            description="Get count of slow queries from the MySQL server",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="mysql_execute_safe_query",
            description="Execute a pre-defined safe read-only query by name. Available queries: "
                       "status, threads, qps, replication_status, node_type, topology, "
                       "processlist, slow_queries, uptime, version",
            inputSchema={
                "type": "object",
                "properties": {
                    "query_name": {
                        "type": "string",
                        "description": "Name of the whitelisted query to execute",
                        "enum": [
                            "status", "variables", "uptime", "version",
                            "threads", "thread_count", "connection_count",
                            "max_connections", "active_connections",
                            "qps", "query_stats", "slow_queries",
                            "replica_status", "slave_status",
                            "replica_hosts", "slave_hosts",
                            "processlist", "read_only", "server_id",
                            "binary_log", "innodb_status", "innodb_metrics"
                        ],
                    }
                },
                "required": ["query_name"],
            },
        ),
        Tool(
            name="mysql_ask_question",
            description="Ask a natural language question about MySQL status. Examples: "
                       "'Is there replication lag?', 'How many threads are running?', "
                       "'What is the QPS average?', 'Is this node a replica?'",
            inputSchema={
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "The natural language question to ask about MySQL",
                    }
                },
                "required": ["question"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """Execute a MySQL tool."""
    agent = get_agent()

    try:
        if name == "mysql_get_uptime":
            data = agent.metrics.get_uptime()
            return [types.TextContent(type="text", text=json.dumps(data, indent=2, default=str))]

        elif name == "mysql_get_thread_stats":
            data = agent.metrics.get_thread_stats()
            return [types.TextContent(type="text", text=json.dumps(data, indent=2, default=str))]

        elif name == "mysql_get_qps":
            data = agent.metrics.get_qps_stats()
            # Calculate actual QPS if we have uptime
            uptime_data = agent.metrics.get_uptime()
            if "uptime_seconds" in uptime_data and "total_queries" in data:
                uptime = uptime_data["uptime_seconds"]
                queries = data["total_queries"]
                if uptime > 0:
                    data["qps_average"] = round(queries / uptime, 2)
            return [types.TextContent(type="text", text=json.dumps(data, indent=2, default=str))]

        elif name == "mysql_get_replication_status":
            data = agent.metrics.get_replication_status()
            return [types.TextContent(type="text", text=json.dumps(data, indent=2, default=str))]

        elif name == "mysql_get_node_type":
            data = agent.metrics.get_node_type()
            return [types.TextContent(type="text", text=json.dumps(data, indent=2, default=str))]

        elif name == "mysql_get_replication_topology":
            data = agent.metrics.get_replication_topology()
            return [types.TextContent(type="text", text=json.dumps(data, indent=2, default=str))]

        elif name == "mysql_get_processlist":
            result = agent.execute_template_query("processlist")
            return [types.TextContent(type="text", text=json.dumps(result, indent=2, default=str))]

        elif name == "mysql_get_slow_queries":
            result = agent.execute_template_query("slow_queries")
            return [types.TextContent(type="text", text=json.dumps(result, indent=2, default=str))]

        elif name == "mysql_execute_safe_query":
            query_name = arguments.get("query_name")
            if not query_name:
                return [types.TextContent(type="text", text="Error: query_name is required")]
            result = agent.execute_template_query(query_name)
            return [types.TextContent(type="text", text=json.dumps(result, indent=2, default=str))]

        elif name == "mysql_ask_question":
            question = arguments.get("question", "")
            if not question:
                return [types.TextContent(type="text", text="Error: question is required")]
            response = agent.ask(question)
            return [types.TextContent(type="text", text=response)]

        else:
            return [types.TextContent(type="text", text=f"Unknown tool: {name}")]

    except QueryNotAllowedError as e:
        return [types.TextContent(type="text", text=f"Security Error: {e}")]
    except MySQLConnectionError as e:
        return [types.TextContent(type="text", text=f"Connection Error: {e}")]
    except Exception as e:
        return [types.TextContent(type="text", text=f"Error: {e}")]


async def main():
    """Run the MCP server."""
    # Initialize the agent connection
    try:
        agent = get_agent()
        print(f"Connected to MySQL at {agent.db.config.host}:{agent.db.config.port}", file=os.stderr)
    except Exception as e:
        print(f"Failed to connect to MySQL: {e}", file=os.stderr)
        raise

    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="mysql-dbre-agent",
                server_version="1.0.0",
                capabilities=app.get_capabilities(),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
