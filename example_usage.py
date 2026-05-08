"""Example usage of the MySQL DBRE Agent programmatically."""

import os
from dotenv import load_dotenv

from agent import MySQLDBREAgent
from config import MySQLConfig

load_dotenv()


def main():
    """Demonstrate agent usage."""
    # Create configuration
    db_config = MySQLConfig.from_env()

    # Create the agent
    agent = MySQLDBREAgent(
        db_config=db_config,
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
    )

    # Connect to database
    agent.connect()
    print("Connected to MySQL!")
    print()

    try:
        # Example 1: Check uptime
        print("1. Checking uptime...")
        response = agent.ask("What is the uptime?")
        print(response)
        print()

        # Example 2: Check threads
        print("2. Checking thread statistics...")
        response = agent.ask("How many threads are running?")
        print(response)
        print()

        # Example 3: Check QPS
        print("3. Checking QPS...")
        response = agent.ask("What are the queries per second?")
        print(response)
        print()

        # Example 4: Check node type
        print("4. Checking node type...")
        response = agent.ask("Is this a primary or replica?")
        print(response)
        print()

        # Example 5: Check replication
        print("5. Checking replication status...")
        response = agent.ask("What is the replication status?")
        print(response)
        print()

        # Example 6: Check topology
        print("6. Checking replication topology...")
        response = agent.ask("What is the replication topology?")
        print(response)
        print()

        # Example 7: Execute a specific whitelisted query
        print("7. Executing specific query template...")
        result = agent.execute_template_query("processlist")
        print(f"Active processes: {result['row_count']}")
        for row in result['rows'][:5]:  # Show first 5
            print(f"  - ID {row.get('ID')}: {row.get('COMMAND')} from {row.get('HOST')}")

    finally:
        agent.disconnect()
        print("\nDisconnected.")


if __name__ == "__main__":
    main()
