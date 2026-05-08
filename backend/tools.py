"""Tool definitions for Claude API integration."""

MYSQL_TOOLS = [
    {
        "name": "mysql_get_uptime",
        "description": "Get MySQL server uptime in seconds and human-readable format",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "mysql_get_thread_stats",
        "description": "Get current thread statistics (running, connected, max connections)",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "mysql_get_qps",
        "description": "Get queries per second (QPS) metrics",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "mysql_get_replication_status",
        "description": "Get replication status including lag and thread status",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "mysql_get_node_type",
        "description": "Identify if the node is a Primary or Read Replica",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "mysql_get_replication_topology",
        "description": "Get the complete replication topology",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "mysql_get_processlist",
        "description": "Get active MySQL processes and queries",
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of processes to return (default 50)",
                    "default": 50
                }
            },
            "required": []
        }
    },
    {
        "name": "mysql_get_slow_queries",
        "description": "Get count of slow queries",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "mysql_execute_safe_query",
        "description": "Execute a predefined whitelisted query",
        "input_schema": {
            "type": "object",
            "properties": {
                "query_name": {
                    "type": "string",
                    "description": "Name of the whitelisted query to execute"
                }
            },
            "required": ["query_name"]
        }
    },
    {
        "name": "mysql_ask_question",
        "description": "Ask a natural language question about MySQL",
        "input_schema": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "Natural language question about MySQL"
                }
            },
            "required": ["question"]
        }
    }
]
