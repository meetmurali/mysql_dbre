"""Main entry point for MySQL DBRE Agent."""

import os
import sys
import logging
from pathlib import Path

from dotenv import load_dotenv

from agent import MySQLDBREAgent, DBREAgentCLI
from config import MySQLConfig

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point."""
    # Check for help
    if len(sys.argv) > 1 and sys.argv[1] in ["-h", "--help"]:
        print("Usage: python main.py [options]")
        print()
        print("Environment variables:")
        print("  MYSQL_HOST        - MySQL host (default: localhost)")
        print("  MYSQL_PORT        - MySQL port (default: 3306)")
        print("  MYSQL_USER        - MySQL username")
        print("  MYSQL_PASSWORD    - MySQL password")
        print("  MYSQL_DATABASE    - Default database (default: information_schema)")
        print("  ANTHROPIC_API_KEY - Optional: for enhanced natural language responses")
        print()
        print("Example:")
        print("  export MYSQL_HOST=mydb.example.com")
        print("  export MYSQL_USER=dbre_agent")
        print("  export MYSQL_PASSWORD=secret")
        print("  python main.py")
        return 0

    # Create agent configuration
    db_config = MySQLConfig.from_env()

    # Validate required settings
    if not db_config.password:
        print("Error: MYSQL_PASSWORD environment variable is required")
        print("Set it with: export MYSQL_PASSWORD=your_password")
        return 1

    # Create the agent
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    agent = MySQLDBREAgent(
        db_config=db_config,
        anthropic_api_key=anthropic_api_key,
    )

    # Run the CLI
    cli = DBREAgentCLI(agent)
    cli.run()

    return 0


if __name__ == "__main__":
    sys.exit(main())
