"""MySQL DBRE Agent - Natural language interface for MySQL metrics."""

import json
import logging
from typing import Dict, Any, Optional, List

from anthropic import Anthropic

from database import MySQLDBREConnection, MySQLMetricsCollector, QueryNotAllowedError
from queries import list_available_queries
from config import MySQLConfig

logger = logging.getLogger(__name__)


class MySQLDBREAgent:
    """Agent for answering MySQL database questions in natural language."""

    SYSTEM_PROMPT = """You are a MySQL Database Reliability Engineering (DBRE) Agent.
Your role is to help users understand their MySQL database status by querying read-only metrics.

IMPORTANT CONSTRAINTS:
- You can ONLY perform read-only operations
- You CANNOT execute DELETE, DROP, TRUNCATE, UPDATE, INSERT, ALTER, or any data-modifying statements
- You work with a whitelist of safe queries only

When answering questions:
1. Explain what information you're retrieving
2. Present the data clearly
3. Provide context about what the metrics mean
4. Highlight any potential issues you notice

If you don't have access to certain information, clearly state that.
"""

    def __init__(
        self,
        db_config: Optional[MySQLConfig] = None,
        anthropic_api_key: Optional[str] = None,
    ):
        self.db = MySQLDBREConnection(db_config)
        self.metrics = MySQLMetricsCollector(self.db)
        self.client: Optional[Anthropic] = None
        if anthropic_api_key:
            self.client = Anthropic(api_key=anthropic_api_key)

    def connect(self) -> None:
        """Connect to MySQL."""
        self.db.connect()

    def disconnect(self) -> None:
        """Disconnect from MySQL."""
        self.db.disconnect()

    def _get_raw_metrics(self, metric_type: str) -> Dict[str, Any]:
        """Collect raw metrics based on type."""
        try:
            if metric_type == "uptime":
                return self.metrics.get_uptime()
            elif metric_type == "threads":
                return self.metrics.get_thread_stats()
            elif metric_type == "qps":
                return self.metrics.get_qps_stats()
            elif metric_type == "replication":
                return self.metrics.get_replication_status()
            elif metric_type == "node_type":
                return self.metrics.get_node_type()
            elif metric_type == "topology":
                return self.metrics.get_replication_topology()
            else:
                return {"error": f"Unknown metric type: {metric_type}"}
        except Exception as e:
            return {"error": str(e)}

    def ask(self, question: str) -> str:
        """Answer a natural language question about MySQL.

        Args:
            question: The user's question

        Returns:
            A natural language response
        """
        # Ensure we're connected
        if not self.db.is_connected():
            self.connect()

        # Parse the question and collect relevant metrics
        collected_data = self._collect_relevant_data(question)

        # If we have Claude API, use it for natural language response
        if self.client:
            return self._ask_claude(question, collected_data)

        # Otherwise, return formatted raw data
        return self._format_response(question, collected_data)

    def _collect_relevant_data(self, question: str) -> Dict[str, Any]:
        """Collect metrics relevant to the user's question."""
        question_lower = question.lower()
        data = {"question": question}

        # Check for various topics in the question
        if any(word in question_lower for word in ["uptime", "up time", "running for"]):
            data["uptime"] = self.metrics.get_uptime()

        if any(word in question_lower for word in ["thread", "connection", "connected"]):
            data["threads"] = self.metrics.get_thread_stats()

        if any(word in question_lower for word in ["qps", "queries per second", "query rate", "queries"]):
            data["qps"] = self.metrics.get_qps_stats()
            data["uptime"] = self.metrics.get_uptime()  # Need this for QPS calculation

        if any(word in question_lower for word in ["replication", "replica", "slave", "lag", "behind"]):
            data["replication"] = self.metrics.get_replication_status()

        if any(word in question_lower for word in ["node type", "primary", "master", "read replica", "server type"]):
            data["node_type"] = self.metrics.get_node_type()

        if any(word in question_lower for word in ["topology", "setup", "configuration"]):
            data["topology"] = self.metrics.get_replication_topology()

        # If no specific topic matched, get general status
        if len(data) == 1:  # Only has "question"
            data["uptime"] = self.metrics.get_uptime()
            data["threads"] = self.metrics.get_thread_stats()
            data["node_type"] = self.metrics.get_node_type()

        return data

    def _ask_claude(self, question: str, data: Dict[str, Any]) -> str:
        """Use Claude API to generate a natural language response."""
        if not self.client:
            return self._format_response(question, data)

        prompt = f"""The user asked about their MySQL database: "{question}"

Here is the data collected from the database:
```json
{json.dumps(data, indent=2, default=str)}
```

Please provide a helpful, natural language response explaining this data.
Be concise but informative. Highlight any important findings or potential issues.
"""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1000,
                system=self.SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Claude API error: {e}")
            return self._format_response(question, data)

    def _format_response(self, question: str, data: Dict[str, Any]) -> str:
        """Format the response without using Claude API."""
        lines = [f"Question: {question}", "", "--- Database Metrics ---", ""]

        for key, value in data.items():
            if key == "question":
                continue
            lines.append(f"{key.upper()}:")
            lines.append(json.dumps(value, indent=2, default=str))
            lines.append("")

        return "\n".join(lines)

    def get_available_queries(self) -> Dict[str, str]:
        """List all available query types."""
        return list_available_queries()

    def execute_template_query(self, query_name: str) -> Dict[str, Any]:
        """Execute a whitelisted query by name."""
        if not self.db.is_connected():
            self.connect()
        return self.db.execute_safe_query(query_name=query_name)


class DBREAgentCLI:
    """Command-line interface for the DBRE Agent."""

    def __init__(self, agent: MySQLDBREAgent):
        self.agent = agent

    def run(self) -> None:
        """Run the interactive CLI."""
        print("=" * 60)
        print("MySQL DBRE Agent - Read-Only Database Assistant")
        print("=" * 60)
        print()

        try:
            self.agent.connect()
            server_info = self.agent.db.get_server_info()
            print(f"Connected to MySQL {server_info['server_version']} at {server_info['host']}")
            print()
        except Exception as e:
            print(f"Failed to connect: {e}")
            return

        print("Available commands:")
        print("  uptime     - Show server uptime")
        print("  threads    - Show thread statistics")
        print("  qps        - Show queries per second")
        print("  replication - Show replication status")
        print("  nodetype   - Show if this is Primary or Replica")
        print("  topology   - Show replication topology")
        print("  status     - Show general status")
        print("  queries    - List available query templates")
        print("  quit       - Exit the agent")
        print()
        print("Or ask natural language questions like:")
        print('  "What is the replication lag?"')
        print('  "How many threads are running?"')
        print()

        while True:
            try:
                user_input = input("> ").strip()

                if not user_input:
                    continue

                if user_input.lower() in ["quit", "exit", "q"]:
                    break

                # Handle quick commands
                if user_input.lower() == "uptime":
                    user_input = "What is the uptime?"
                elif user_input.lower() == "threads":
                    user_input = "How many threads are running?"
                elif user_input.lower() == "qps":
                    user_input = "What is the QPS?"
                elif user_input.lower() == "replication":
                    user_input = "What is the replication status?"
                elif user_input.lower() == "nodetype":
                    user_input = "Is this a primary or replica node?"
                elif user_input.lower() == "topology":
                    user_input = "What is the replication topology?"
                elif user_input.lower() == "status":
                    user_input = "Show general status"
                elif user_input.lower() == "queries":
                    queries = self.agent.get_available_queries()
                    print("\nAvailable query templates:")
                    for name, desc in queries.items():
                        print(f"  {name}: {desc}")
                    print()
                    continue

                # Process the question
                print()
                response = self.agent.ask(user_input)
                print(response)
                print()

            except QueryNotAllowedError as e:
                print(f"Error: {e}")
                print("This agent only supports read-only operations.")
            except KeyboardInterrupt:
                print("\nUse 'quit' to exit.")
            except Exception as e:
                print(f"Error: {e}")

        print("Goodbye!")
        self.agent.disconnect()
