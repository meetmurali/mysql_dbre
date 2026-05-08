# MySQL DBRE Agent

A Database Reliability Engineering agent for MySQL that provides read-only access to database metadata and real-time statistics.

## Features

- **Read-only operations only** - Strictly prohibited from DELETE, DROP, UPDATE, INSERT, etc.
- Real-time metrics: QPS, thread counts, uptime
- Replication status: lag detection, topology mapping
- Node identification: Primary vs Read Replica

## Requirements

- Python 3.11+ (for MCP server support)
- MySQL 8.0+ (5.7 compatible with older syntax)

## Setup

1. **Install dependencies:**
```bash
# Use Python 3.11+ for MCP support
pip3.11 install -r requirements.txt
```

2. **Configure environment variables in `.env`:**
```
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=dbre_agent
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=information_schema
```

3. **Run the agent:**
```bash
python3.11 main.py
```

## Safety

This agent only runs whitelisted read-only queries. Any attempt to execute destructive operations will be blocked.

---

## Running as an MCP Server

The MySQL DBRE Agent can also run as an MCP (Model Context Protocol) server, allowing Claude Code to use it as a tool.

### MCP Server Tools

When running as an MCP server, the following tools are available:

| Tool | Description |
|------|-------------|
| `mysql_get_uptime` | Server uptime in seconds and human-readable format |
| `mysql_get_thread_stats` | Thread statistics (running, connected, max) |
| `mysql_get_qps` | Queries per second metrics |
| `mysql_get_replication_status` | Replication lag, IO/SQL thread status |
| `mysql_get_node_type` | Primary vs Replica identification |
| `mysql_get_replication_topology` | Full replication topology |
| `mysql_get_processlist` | Active processes and queries |
| `mysql_get_slow_queries` | Count of slow queries |
| `mysql_execute_safe_query` | Execute predefined whitelisted query |
| `mysql_ask_question` | Natural language questions about MySQL |

### Setup for Claude Code

#### Option 1: Using the Install Script (Recommended)

```bash
# Ensure dependencies are installed with Python 3.11+
pip3.11 install -r requirements.txt

# Run the install script
./install_mcp.sh
```

This will create or update your Claude Code settings file with the MCP server configuration.

#### Option 2: Manual Configuration

1. **Install MCP SDK (requires Python 3.11+):**
```bash
pip3.11 install mcp>=1.0.0
```

2. **Configure Claude Code settings:**

Create or edit your Claude Code settings file:
- **macOS**: `~/Library/Application Support/Claude/settings.json`
- **Linux**: `~/.config/claude/settings.json`

```json
{
  "mcpServers": {
    "mysql-dbre-agent": {
      "command": "python3.11",
      "args": ["/full/path/to/mysql_agent/mcp_server.py"],
      "env": {
        "MYSQL_HOST": "localhost",
        "MYSQL_PORT": "3306",
        "MYSQL_USER": "dbre_agent",
        "MYSQL_PASSWORD": "your_password",
        "MYSQL_DATABASE": "information_schema"
      }
    }
  }
}
```

Or use environment variable substitution:
```json
{
  "mcpServers": {
    "mysql-dbre-agent": {
      "command": "python3.11",
      "args": ["/full/path/to/mysql_agent/mcp_server.py"],
      "env": {
        "MYSQL_HOST": "${MYSQL_HOST}",
        "MYSQL_PORT": "${MYSQL_PORT}",
        "MYSQL_USER": "${MYSQL_USER}",
        "MYSQL_PASSWORD": "${MYSQL_PASSWORD}",
        "MYSQL_DATABASE": "${MYSQL_DATABASE}"
      }
    }
  }
}
```

3. **Alternative: Set up via `.env` file:**

The MCP server will automatically load environment variables from `.env` file, so you can also just ensure your `.env` file is configured and the MCP server will read from it.

4. **Restart Claude Code** to load the new MCP server.

### Testing the MCP Server

Once configured, you can ask Claude questions like:

- "What is the replication lag on my MySQL server?"
- "How many threads are currently running?"
- "Is this MySQL node a primary or replica?"
- "Show me the replication topology"
- "What is the QPS on the database?"

Claude will automatically use the appropriate MCP tools to answer these questions.
