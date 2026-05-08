"""MySQL database connection and safe query execution."""

from typing import Optional, List, Dict, Any, Tuple
import logging
import os

import mysql.connector
from mysql.connector import Error, pooling

from config import MySQLConfig
from queries import is_query_allowed, get_query_template, QueryTemplate

logger = logging.getLogger(__name__)


class MySQLConnectionError(Exception):
    """Raised when MySQL connection fails."""
    pass


class QueryNotAllowedError(Exception):
    """Raised when a query is not in the whitelist."""
    pass


class MySQLDBREConnection:
    """Manages MySQL connections for the DBRE Agent."""

    def __init__(self, config: Optional[MySQLConfig] = None):
        self.config = config or MySQLConfig.from_env()
        self._connection: Optional[mysql.connector.MySQLConnection] = None
        self._pool: Optional[pooling.MySQLConnectionPool] = None

    def connect(self) -> None:
        """Establish connection to MySQL server."""
        try:
            # Use a connection pool when requested via env var MYSQL_POOL_SIZE
            pool_size = int(os.getenv("MYSQL_POOL_SIZE", "0"))
            if pool_size and pool_size > 0:
                self._pool = pooling.MySQLConnectionPool(
                    pool_name="dbre_pool",
                    pool_size=pool_size,
                    host=self.config.host,
                    port=self.config.port,
                    user=self.config.user,
                    password=self.config.password,
                    database=self.config.database,
                    ssl_disabled=self.config.ssl_disabled,
                    connection_timeout=self.config.connect_timeout,
                    autocommit=True,
                )
                # Acquire one connection as the primary connection for compatibility
                self._connection = self._pool.get_connection()
            else:
                self._connection = mysql.connector.connect(
                    host=self.config.host,
                    port=self.config.port,
                    user=self.config.user,
                    password=self.config.password,
                    database=self.config.database,
                    ssl_disabled=self.config.ssl_disabled,
                    connect_timeout=self.config.connect_timeout,
                    autocommit=True,
                )
            logger.info(f"Connected to MySQL at {self.config.host}:{self.config.port}")
        except Error as e:
            raise MySQLConnectionError(f"Failed to connect to MySQL: {e}")

    def disconnect(self) -> None:
        """Close the MySQL connection."""
        try:
            if self._connection and getattr(self._connection, "is_connected", lambda: False)():
                self._connection.close()
            # Close pooled connections if any
            if self._pool:
                try:
                    # mysql.connector pools close connections automatically; clear reference
                    self._pool = None
                except Exception:
                    pass
        finally:
            logger.info("MySQL connection closed")

    def is_connected(self) -> bool:
        """Check if connection is active."""
        return self._connection is not None and self._connection.is_connected()

    def ensure_connected(self) -> None:
        """Ensure connection is established, reconnect if needed."""
        if not self.is_connected():
            self.connect()

    def execute_safe_query(
        self,
        query_name: Optional[str] = None,
        sql: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute a whitelisted read-only query.

        Args:
            query_name: Name of the whitelisted query template
            sql: Raw SQL (must pass safety checks)

        Returns:
            Dictionary with columns, rows, and row count

        Raises:
            QueryNotAllowedError: If query is not allowed
            MySQLConnectionError: If execution fails
        """
        self.ensure_connected()

        # Determine the SQL to execute
        if query_name:
            template = get_query_template(query_name)
            if not template:
                raise QueryNotAllowedError(f"Unknown query template: {query_name}")
            sql = template.sql
        elif sql:
            # Validate the raw SQL
            allowed, error = is_query_allowed(sql)
            if not allowed:
                raise QueryNotAllowedError(f"Query not allowed: {error}")
        else:
            raise ValueError("Must provide either query_name or sql")

        logger.debug(f"Executing query: {sql[:100]}...")

        # Debug: log the full SQL for troubleshooting
        logger.debug(f"Full SQL: {sql}")

        # Use pooled connection if available to isolate cursors per call
        conn = None
        try:
            if self._pool:
                conn = self._pool.get_connection()
            else:
                conn = self._connection

            if conn is None:
                raise MySQLConnectionError("No active MySQL connection")

            cursor = conn.cursor(dictionary=True)
            cursor.execute(sql)

            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            logger.debug(f"Query columns: {columns}")
            logger.debug(f"First row (if any): {rows[0] if rows else None}")
            row_count = cursor.rowcount

            cursor.close()

            return {
                "columns": columns,
                "rows": rows,
                "row_count": row_count,
                **({
                    "debug_sql": sql,
                    "debug_first_row": rows[0] if rows else None,
                } if os.getenv("MYSQL_AGENT_DEBUG", "False").lower() == "true" else {}),
            }

        except Error as e:
            raise MySQLConnectionError(f"Query execution failed: {e}")
        finally:
            # If we acquired a pooled connection, release it
            try:
                if self._pool and conn is not None:
                    conn.close()
            except Exception:
                pass

    def execute_show_command(self, command: str) -> Dict[str, Any]:
        """Execute a SHOW command safely.

        Args:
            command: The SHOW command (e.g., "SHOW GLOBAL STATUS")

        Returns:
            Dictionary with query results
        """
        command_upper = command.upper().strip()

        # Only allow SHOW commands
        if not command_upper.startswith("SHOW"):
            raise QueryNotAllowedError("Only SHOW commands are allowed")

        return self.execute_safe_query(sql=command)

    def get_server_info(self) -> Dict[str, Any]:
        """Get basic server information."""
        self.ensure_connected()
        return {
            "server_version": self._connection.get_server_info(),
            "host": self.config.host,
            "port": self.config.port,
            "database": self.config.database,
        }


class MySQLMetricsCollector:
    """Collects and formats MySQL metrics for the agent."""

    def __init__(self, connection: MySQLDBREConnection):
        self.conn = connection

    def get_uptime(self) -> Dict[str, Any]:
        """Get server uptime in human-readable format."""
        result = self.conn.execute_safe_query(query_name="uptime")
        if result["rows"]:
            row = result["rows"][0]

            # Try to find a numeric uptime value in the returned row.
            uptime_seconds = None
            # Common column names: 'Value' (SHOW), 'VARIABLE_VALUE', 'uptime' (SELECT @@GLOBAL.uptime)
            for key, val in row.items():
                if val is None:
                    continue
                try:
                    uptime_seconds = int(float(val))
                    break
                except Exception:
                    continue

            if uptime_seconds is None:
                return {"error": "Could not parse uptime from database response", "raw_row": row}

            days = uptime_seconds // 86400
            hours = (uptime_seconds % 86400) // 3600
            minutes = (uptime_seconds % 3600) // 60
            return {
                "uptime_seconds": uptime_seconds,
                "uptime_formatted": f"{days}d {hours}h {minutes}m",
            }

        return {"error": "Could not retrieve uptime"}

    def get_thread_stats(self) -> Dict[str, Any]:
        """Get comprehensive thread statistics."""
        stats = {}
        # Running threads
        result = self.conn.execute_safe_query(query_name="thread_count")
        if result["rows"]:
            row = result["rows"][0]
            val = None
            for v in row.values():
                try:
                    val = int(float(v))
                    break
                except Exception:
                    continue
            stats["threads_running"] = val or 0

        # Connected threads
        result = self.conn.execute_safe_query(query_name="active_connections")
        if result["rows"]:
            row = result["rows"][0]
            val = None
            for v in row.values():
                try:
                    val = int(float(v))
                    break
                except Exception:
                    continue
            stats["threads_connected"] = val or 0

        # Max connections
        result = self.conn.execute_safe_query(query_name="max_connections")
        if result["rows"]:
            row = result["rows"][0]
            val = None
            for v in row.values():
                try:
                    val = int(float(v))
                    break
                except Exception:
                    continue
            stats["max_connections"] = val or 0

        return stats

    def get_qps_stats(self) -> Dict[str, Any]:
        """Get queries per second statistics."""
        result = self.conn.execute_safe_query(query_name="qps")
        if result["rows"]:
            row = result["rows"][0]
            questions = None
            for v in row.values():
                try:
                    questions = int(float(v))
                    break
                except Exception:
                    continue
            if questions is None:
                return {"error": "Could not parse total queries", "raw_row": row}
            return {
                "total_queries": questions,
                "note": "QPS requires calculating questions/time. Use get_uptime() for time.",
            }
        return {"error": "Could not retrieve QPS stats"}

    def get_version(self) -> Dict[str, Any]:
        """Get MySQL server version."""
        result = self.conn.execute_safe_query(query_name="version")
        if result["rows"]:
            row = result["rows"][0]
            for v in row.values():
                if v is not None:
                    return {"version": str(v)}
        return {"error": "Could not retrieve version"}

    def get_replication_status(self) -> Dict[str, Any]:
        """Get replication status, handling different MySQL versions."""
        # Try modern syntax first (MySQL 8.0+)
        try:
            result = self.conn.execute_safe_query(query_name="replica_status")
            if result["rows"]:
                row = result["rows"][0]
                return {
                    "is_replica": True,
                    "io_thread_running": row.get("Replica_IO_Running"),
                    "sql_thread_running": row.get("Replica_SQL_Running"),
                    "lag_seconds": row.get("Seconds_Behind_Source"),
                    "source_host": row.get("Source_Host"),
                    "source_port": row.get("Source_Port"),
                    "last_error": row.get("Last_Error"),
                }
        except Exception:
            pass

        # Try older syntax (MySQL 5.7 and earlier)
        try:
            result = self.conn.execute_safe_query(query_name="slave_status")
            if result["rows"]:
                row = result["rows"][0]
                return {
                    "is_replica": True,
                    "io_thread_running": row.get("Slave_IO_Running"),
                    "sql_thread_running": row.get("Slave_SQL_Running"),
                    "lag_seconds": row.get("Seconds_Behind_Master"),
                    "source_host": row.get("Master_Host"),
                    "source_port": row.get("Master_Port"),
                    "last_error": row.get("Last_Error"),
                }
        except Exception:
            pass

        return {"is_replica": False, "message": "This node is not a replica"}

    def get_node_type(self) -> Dict[str, Any]:
        """Determine if this is a primary or replica node."""
        # Check read_only variable
        result = self.conn.execute_safe_query(query_name="read_only")
        is_read_only = False
        if result["rows"]:
            is_read_only = result["rows"][0].get("Value", "OFF") == "ON"

        # Check if binary logging is enabled (indicates potential primary)
        result = self.conn.execute_safe_query(query_name="binary_log")
        has_binary_log = False
        if result["rows"]:
            has_binary_log = result["rows"][0].get("Value", "OFF") == "ON"

        # Check replication status
        replication = self.get_replication_status()
        is_replica = replication.get("is_replica", False)

        node_type = "unknown"
        if is_read_only and is_replica:
            node_type = "read_replica"
        elif not is_read_only and has_binary_log and not is_replica:
            node_type = "primary"
        elif not is_read_only and is_replica:
            node_type = "primary_with_replica"
        elif is_read_only and not is_replica:
            node_type = "read_only_standalone"

        return {
            "node_type": node_type,
            "is_read_only": is_read_only,
            "is_replica": is_replica,
            "has_binary_log": has_binary_log,
        }

    def get_replication_topology(self) -> Dict[str, Any]:
        """Get replication topology information."""
        topology = {
            "current_node": {},
            "replicas": [],
        }

        # Get current node info
        result = self.conn.execute_safe_query(query_name="server_id")
        if result["rows"]:
            topology["current_node"]["server_id"] = result["rows"][0].get("Value")

        # Get node type
        node_info = self.get_node_type()
        topology["current_node"].update(node_info)

        # Try to get connected replicas
        try:
            result = self.conn.execute_safe_query(query_name="replica_hosts")
            topology["replicas"] = result["rows"]
        except Exception:
            try:
                result = self.conn.execute_safe_query(query_name="slave_hosts")
                topology["replicas"] = result["rows"]
            except Exception:
                pass

        return topology
