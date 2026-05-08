"""Whitelisted read-only queries for MySQL DBRE Agent.

This module defines the ONLY queries that the agent is allowed to execute.
Any query not in this whitelist will be rejected.
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional, Any


@dataclass
class QueryTemplate:
    """A whitelisted query template with metadata."""

    name: str
    description: str
    sql: str
    required_params: List[str] = None

    def __post_init__(self):
        if self.required_params is None:
            self.required_params = []


# Whitelisted read-only queries
# These are the ONLY queries the agent can execute
WHITELISTED_QUERIES: Dict[str, QueryTemplate] = {
    # Status and Uptime
    "status": QueryTemplate(
        name="status",
        description="Show global status variables",
        sql="SHOW GLOBAL STATUS",
    ),
    "variables": QueryTemplate(
        name="variables",
        description="Show global system variables",
        sql="SHOW GLOBAL VARIABLES",
    ),
    "uptime": QueryTemplate(
        name="uptime",
        description="Get server uptime in seconds (reliable numeric value)",
        sql="SHOW GLOBAL status LIKE 'uptime'",
    ),
    "version": QueryTemplate(
        name="version",
        description="Get MySQL server version",
        sql="SELECT VERSION() as version",
    ),
    # Thread and Connection Info
    "threads": QueryTemplate(
        name="threads",
        description="Get current thread statistics",
        sql="""
            SELECT
                THREAD_ID,
                NAME,
                PROCESSLIST_ID,
                PROCESSLIST_USER,
                PROCESSLIST_HOST,
                PROCESSLIST_DB,
                PROCESSLIST_COMMAND,
                PROCESSLIST_STATE,
                PROCESSLIST_TIME,
                PROCESSLIST_INFO
            FROM performance_schema.threads
            WHERE TYPE = 'FOREGROUND'
            ORDER BY PROCESSLIST_TIME DESC
        """,
    ),
    "thread_count": QueryTemplate(
        name="thread_count",
        description="Get count of running threads",
        sql="SHOW GLOBAL STATUS LIKE 'Threads_running'",
    ),
    "connection_count": QueryTemplate(
        name="connection_count",
        description="Get total connection count",
        sql="SHOW GLOBAL STATUS LIKE 'Connections'",
    ),
    "max_connections": QueryTemplate(
        name="max_connections",
        description="Get maximum allowed connections",
        sql="SHOW GLOBAL VARIABLES LIKE 'max_connections'",
    ),
    "active_connections": QueryTemplate(
        name="active_connections",
        description="Get currently connected threads",
        sql="SHOW GLOBAL STATUS LIKE 'Threads_connected'",
    ),
    # Query Performance
    "qps": QueryTemplate(
        name="qps",
        description="Get queries per second (Questions since startup)",
        sql="SHOW GLOBAL STATUS LIKE 'Questions'",
    ),
    "query_stats": QueryTemplate(
        name="query_stats",
        description="Get query-related statistics",
        sql="""
            SELECT
                VARIABLE_NAME,
                VARIABLE_VALUE
            FROM performance_schema.global_status
            WHERE VARIABLE_NAME IN (
                'Questions', 'Queries', 'Slow_queries',
                'Com_select', 'Com_insert', 'Com_update',
                'Com_delete', 'Com_replace'
            )
        """,
    ),
    "slow_queries": QueryTemplate(
        name="slow_queries",
        description="Get slow query count",
        sql="SHOW GLOBAL STATUS LIKE 'Slow_queries'",
    ),
    # Replication Status
    "replica_status": QueryTemplate(
        name="replica_status",
        description="Get replication status (MySQL 8.0+)",
        sql="SHOW REPLICA STATUS",
    ),
    "slave_status": QueryTemplate(
        name="slave_status",
        description="Get replication status (MySQL 5.7 and older)",
        sql="SHOW SLAVE STATUS",
    ),
    "replica_hosts": QueryTemplate(
        name="replica_hosts",
        description="Get list of connected replicas",
        sql="SHOW REPLICA HOSTS",
    ),
    "slave_hosts": QueryTemplate(
        name="slave_hosts",
        description="Get list of connected slaves (older versions)",
        sql="SHOW SLAVE HOSTS",
    ),
    # Process List
    "processlist": QueryTemplate(
        name="processlist",
        description="Get current process list",
        sql="""
            SELECT
                ID,
                USER,
                HOST,
                DB,
                COMMAND,
                TIME,
                STATE,
                LEFT(INFO, 100) as INFO
            FROM information_schema.PROCESSLIST
            WHERE COMMAND != 'Sleep'
            ORDER BY TIME DESC
            LIMIT 50
        """,
    ),
    # Node Info
    "read_only": QueryTemplate(
        name="read_only",
        description="Check if server is in read-only mode",
        sql="SHOW GLOBAL VARIABLES LIKE 'read_only'",
    ),
    "server_id": QueryTemplate(
        name="server_id",
        description="Get server ID",
        sql="SHOW GLOBAL VARIABLES LIKE 'server_id'",
    ),
    "binary_log": QueryTemplate(
        name="binary_log",
        description="Check if binary logging is enabled",
        sql="SHOW GLOBAL VARIABLES LIKE 'log_bin'",
    ),
    # InnoDB Status
    "innodb_status": QueryTemplate(
        name="innodb_status",
        description="Get InnoDB status",
        sql="SHOW ENGINE INNODB STATUS",
    ),
    "innodb_metrics": QueryTemplate(
        name="innodb_metrics",
        description="Get InnoDB metrics",
        sql="""
            SELECT
                NAME,
                COUNT
            FROM information_schema.INNODB_METRICS
            WHERE STATUS = 'enabled'
            LIMIT 50
        """,
    ),
}

# Forbidden keywords that will cause immediate rejection
FORBIDDEN_KEYWORDS = [
    "DELETE",
    "DROP",
    "TRUNCATE",
    "UPDATE",
    "INSERT",
    "REPLACE",
    "ALTER",
    "CREATE",
    "GRANT",
    "REVOKE",
    "FLUSH",
    "RESET",
    "KILL",
    "SHUTDOWN",
    "RESTART",
]


def is_query_allowed(query: str) -> Tuple[bool, Optional[str]]:
    """Check if a query is in the whitelist and doesn't contain forbidden keywords.

    Args:
        query: The SQL query to check

    Returns:
        Tuple of (is_allowed, error_message)
    """
    query_upper = query.upper().strip()

    # Check for forbidden keywords
    for keyword in FORBIDDEN_KEYWORDS:
        if keyword in query_upper:
            return False, f"Forbidden keyword detected: {keyword}"

    # Check if it starts with allowed commands
    allowed_prefixes = ("SELECT", "SHOW")
    if not any(query_upper.startswith(prefix) for prefix in allowed_prefixes):
        return False, "Query must start with SELECT or SHOW"

    return True, None


def get_query_template(name: str) -> Optional[QueryTemplate]:
    """Get a whitelisted query by name.

    Args:
        name: The query template name

    Returns:
        The QueryTemplate if found, None otherwise
    """
    return WHITELISTED_QUERIES.get(name)


def list_available_queries() -> Dict[str, str]:
    """List all available query templates.

    Returns:
        Dictionary mapping query names to descriptions
    """
    return {name: qt.description for name, qt in WHITELISTED_QUERIES.items()}
