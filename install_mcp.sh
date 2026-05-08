#!/bin/bash
# Script to install MySQL DBRE Agent MCP server configuration for Claude Code

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MCP_SERVER_PATH="$SCRIPT_DIR/mcp_server.py"

# Detect OS and set config directory
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    CONFIG_DIR="$HOME/Library/Application Support/Claude"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    CONFIG_DIR="$HOME/.config/claude"
else
    echo "Unsupported OS: $OSTYPE"
    exit 1
fi

# Create config directory if it doesn't exist
mkdir -p "$CONFIG_DIR"

SETTINGS_FILE="$CONFIG_DIR/settings.json"

# Check if settings.json exists
if [ -f "$SETTINGS_FILE" ]; then
    echo "Found existing settings.json at $SETTINGS_FILE"
    echo "Please manually add the following MCP server configuration:"
    echo ""
    cat <<EOF
{
  "mcpServers": {
    "mysql-dbre-agent": {
      "command": "python3.11",
      "args": ["$MCP_SERVER_PATH"],
      "env": {
        "MYSQL_HOST": "${MYSQL_HOST:-localhost}",
        "MYSQL_PORT": "${MYSQL_PORT:-3306}",
        "MYSQL_USER": "${MYSQL_USER:-dbre_agent}",
        "MYSQL_PASSWORD": "${MYSQL_PASSWORD:-}",
        "MYSQL_DATABASE": "${MYSQL_DATABASE:-information_schema}"
      }
    }
  }
}
EOF
else
    echo "Creating new settings.json at $SETTINGS_FILE"
    cat > "$SETTINGS_FILE" <<EOF
{
  "mcpServers": {
    "mysql-dbre-agent": {
      "command": "python3.11",
      "args": ["$MCP_SERVER_PATH"],
      "env": {
        "MYSQL_HOST": "${MYSQL_HOST:-localhost}",
        "MYSQL_PORT": "${MYSQL_PORT:-3306}",
        "MYSQL_USER": "${MYSQL_USER:-dbre_agent}",
        "MYSQL_PASSWORD": "${MYSQL_PASSWORD:-}",
        "MYSQL_DATABASE": "${MYSQL_DATABASE:-information_schema}"
      }
    }
  }
}
EOF
    echo "Created $SETTINGS_FILE"
fi

echo ""
echo "=== Installation Complete ==="
echo ""
echo "MCP server path: $MCP_SERVER_PATH"
echo "Config file: $SETTINGS_FILE"
echo ""
echo "Make sure you have:"
echo "1. Installed dependencies: pip install -r requirements.txt"
echo "2. Set your MySQL credentials in .env or environment variables"
echo "3. Restarted Claude Code to load the MCP server"
echo ""
echo "To test, ask Claude: 'What is the MySQL replication status?'"
