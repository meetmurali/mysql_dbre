# MySQL DBRE Agent — Architecture Overview

## Purpose
This document describes the high-level components, data flow, and runtime dependencies for the MySQL DBRE Agent proof-of-concept: UI → backend → LLM/tool orchestration → MySQL.

## Components

- Frontend (Web UI)
  - Location: frontend/
  - Role: React + Vite app that accepts user messages, displays chat history, and receives Server-Sent Events (SSE) from the backend with tool execution events and final responses.

- Backend API (Chat + Tool Orchestration)
  - Location: backend/main.py
  - Role: Accepts chat POSTs at `/api/chat`, asks the local LLM (Ollama) which tools to call, executes whitelisted read-only tools against the database, then synthesizes and streams a final answer.

- MCP Server Entrypoint (optional)
  - Location: mcp_server.py
  - Role: Exposes tools/resources via the Model Context Protocol (MCP) so external LLMs (e.g., Claude Code) can call tools directly. Note: the project POC uses a locally-hosted Ollama `llama3.2` model for planning and synthesis; MCP support remains available for external LLMs if desired.

- Agent Logic
  - Location: agent.py
  - Role: Wraps DB connection, metrics collector, and an optional remote LLM client (Anthropic) for NL responses. In this POC the default runtime uses the local Ollama client (`llama3.2:latest`) rather than Anthropic/Claude.

- Database Layer
  - Location: database.py
  - Role: Centralized DB connection management (supports optional pooling via `MYSQL_POOL_SIZE`), safe query execution, and `MySQLMetricsCollector` helper methods used by tools.

- Query Whitelist
  - Location: queries.py
  - Role: Enumerates allowed read-only SQL templates and performs safety checks (forbidden keywords) to prevent destructive queries.

- Example & CLI
  - Locations: example_usage.py, main.py
  - Role: Local testing harness and an interactive CLI for manual checks.

- Setup Scripts & Config
  - `.env`: local environment variables (DB creds, Ollama host, pool size)
  - setup_mysql_user.sql: SQL to create the `dbre_agent` read-only user
  - install_mcp.sh: helper to register the MCP server for Claude Code
  - requirements.txt / frontend/package.json: dependency manifests

## End-to-end Data Flow

1. User types a question in the UI and sends it to the backend `/api/chat`.
2. Backend builds the conversation and a system prompt that lists available tools and instructions for the model.
3. Backend calls the local LLM (Ollama) to plan; the model returns a response that may include tool markers like `[TOOL: mysql_get_replication_status limit=20]`.
4. Backend parses tool markers and calls the mapped functions (e.g., `MySQLMetricsCollector.get_replication_status()` or `db_connection.execute_safe_query()`).
5. `database.py` validates queries against `queries.py`, executes them using a pooled or single connection, and returns structured results.
6. Backend provides these real tool results back to the LLM (or formats the reply itself) and streams the final answer and tool events back to the UI as SSE.
7. UI displays both intermediate tool execution events and the final synthesized answer.

## LLM ↔ Tools Interaction

- Planning phase: LLM decides which tools to call based on the system prompt. Backend expects deterministic markers (`[TOOL: ...]`) to find tool calls.
- Execution phase: Backend only runs whitelisted, read-only queries. Raw SQL passed by a user is validated by `is_query_allowed()`.
- Synthesis phase: Backend feeds actual query results back to the LLM for a final, informed response.

## Security & Safety Controls

- Whitelisted queries only (see `queries.py`).
- `FORBIDDEN_KEYWORDS` prevents destructive statements (DELETE, DROP, ALTER, etc.).
- DB user must be least-privilege (see `setup_mysql_user.sql`) — only `SELECT`, `SHOW`, `PROCESS`, `REPLICATION` privileges as needed.
- Store secrets in `.env` (do not commit to source control).
- Backend should avoid logging secrets.

## Runtime Dependencies & Installed Software

- Python 3.11+
  - Packages: `mysql-connector-python`, `fastapi`, `uvicorn`, `ollama`, `python-dotenv`, `pydantic` (see `requirements.txt`).
- Node.js / npm (frontend)
  - Tools: `vite`, React, TypeScript (see `frontend/package.json`).
- Local LLM runtime (Ollama) and model `llama3.2:latest` for on-host inference (this is the POC configuration). Remote LLMs (Anthropic/Claude) are supported optionally by the agent but are not required.
- MySQL server accessible at `MYSQL_HOST`/`MYSQL_PORT` with the `dbre_agent` read-only user.

## Local Dev Quick Commands

```bash
# Backend
python3.11 -m pip install -r requirements.txt
python3.11 -m backend.main

# Frontend
cd frontend
npm ci
npm run dev
# open http://localhost:5173
```

## Troubleshooting Tips

- ModuleNotFoundError: ensure you installed Python deps with the same Python used to run the backend.
- DB connection errors: confirm `.env` values and that `dbre_agent` grants are applied (see `setup_mysql_user.sql`).
- Ollama/model not available: ensure Ollama is running locally and `llama3.2:latest` is installed; otherwise backend can still return tool outputs without synthesis.
- Tool parsing failures: prefer a stricter tool-call token (JSON) to make parsing robust.

## Recommended Next Improvements

- Add integration tests (mock DB results) under `tests/`.
- Replace textual tool markers with a strict JSON-formatted tool-call protocol for reliability.
- Add per-tool timeouts and circuit-breakers.
- Expose a health endpoint that reports DB + LLM availability.
- Add observability: logs, metrics, and error traces.

---

If you'd like, I can commit this file to the repo (already created), or extend it with a diagram or sequence diagram image. Tell me what you'd prefer next.