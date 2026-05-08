# MySQL DBRE Agent - Full Chat Application

A complete web-based chat interface for interacting with your MySQL database using Claude AI with tool-based integration.

## Architecture

- **Backend**: FastAPI server that orchestrates Claude API calls with MySQL tools
- **Frontend**: React + TypeScript SPA with real-time chat UI
- **Database**: Direct integration with MySQL DBRE tools

## Prerequisites

- Python 3.9+ (for backend)
- Node.js 18+ and npm (for frontend)
- MySQL server running with DBRE agent user configured
- Claude API key (`ANTHROPIC_API_KEY`)

## Setup Instructions

### 1. Backend Setup

```bash
# Install Python dependencies (if not done already)
cd /Users/murali/Downloads/mysql_agent
python3 -m pip install -r requirements.txt --user --upgrade

# Verify ANTHROPIC_API_KEY is set
echo $ANTHROPIC_API_KEY
# If empty, set it:
# export ANTHROPIC_API_KEY="sk-ant-..."
```

### 2. Frontend Setup

```bash
# Install Node dependencies (if not done already)
cd /Users/murali/Downloads/mysql_agent/frontend
npm install
```

### 3. Environment Configuration

Make sure your `.env` file has:

```
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=dbre_agent
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=information_schema
ANTHROPIC_API_KEY=sk-ant-...
```

## Running the Application

Open **two** terminal windows:

### Terminal 1: Start Backend

```bash
cd /Users/murali/Downloads/mysql_agent
python3 -m uvicorn backend.main:app --reload --port 8000
```

You should see:
```
Uvicorn running on http://127.0.0.1:8000
```

### Terminal 2: Start Frontend

```bash
cd /Users/murali/Downloads/mysql_agent/frontend
npm run dev
```

You should see:
```
VITE v5.0.0 ready in 123 ms

➜ Local:   http://localhost:5173/
```

### 3. Open Browser

Navigate to: **http://localhost:5173**

## Using the Chat Interface

Once the UI is loaded, you can ask questions like:

- "What is the MySQL server uptime?"
- "How many threads are currently running?"
- "Is this node a primary or replica?"
- "Show me the replication lag"
- "What's the current QPS?"
- "What are the slow queries?"

The assistant will:
1. Use appropriate MySQL tools to gather information
2. Show which tools are being used (collapsible)
3. Provide a natural language response based on the data

## Features

### Chat Interface
- ✅ Real-time message streaming
- ✅ Tool execution visibility (see which tools Claude uses)
- ✅ Collapsible tool details section
- ✅ Loading indicators
- ✅ Error handling and display

### Response Actions
- ✅ Copy individual messages
- ✅ Download messages as .txt files
- ✅ Clear conversation history
- ✅ Markdown formatting for responses

### Backend Features
- ✅ Direct Python tool integration (faster than subprocess MCP)
- ✅ Automatic tool execution
- ✅ Streaming responses via Server-Sent Events (SSE)
- ✅ In-memory conversation history
- ✅ CORS support for localhost development

## API Documentation

### Endpoint: POST /api/chat

**Request:**
```json
{
  "message": "What is the MySQL uptime?",
  "history": [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ]
}
```

**Response:** Server-Sent Events stream
```
data: {"type": "tool_use", "tool": "mysql_get_uptime", "input": {}}
data: {"type": "text", "content": "The server has been running for..."}
```

## Troubleshooting

### Backend won't start
```bash
# Check if port 8000 is in use
lsof -i :8000

# Check Python imports
python3 -c "import backend.main; print('OK')"

# Try a different port
python3 -m uvicorn backend.main:app --port 8001
```

### Frontend won't start
```bash
# Check if port 5173 is in use
lsof -i :5173

# Clear npm cache
npm cache clean --force

# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install
```

### Chat not connecting to backend
1. Verify backend is running on http://localhost:8000
2. Check browser console for CORS errors
3. Verify `ANTHROPIC_API_KEY` is set in backend `.env`
4. Restart both servers

### No database response
1. Verify MySQL server is running
2. Check `.env` file for correct credentials
3. Test MySQL connection:
   ```bash
   python3 -c "from database import MySQLDBREConnection; from config import MySQLConfig; db = MySQLDBREConnection(MySQLConfig.from_env()); db.connect(); print('Connected!')"
   ```

## Development

### Project Structure
```
mysql_agent/
├── backend/
│   ├── main.py           # FastAPI app
│   ├── schemas.py        # Request/response models
│   ├── tools.py          # Claude tool definitions
│   └── __init__.py
├── frontend/
│   ├── src/
│   │   ├── App.tsx       # Main app component
│   │   ├── components/   # React components
│   │   ├── hooks/        # Custom hooks
│   │   ├── types/        # TypeScript types
│   │   └── index.tsx     # Entry point
│   └── package.json
├── agent.py              # Existing agent logic
├── database.py           # MySQL connection
└── requirements.txt
```

### Adding New Tools

1. Add tool definition to `backend/tools.py` in `MYSQL_TOOLS`
2. Add execution logic to `execute_tool()` in `backend/main.py`
3. Tool will automatically be available to Claude

## Production Notes

For production deployment:
- Remove `--reload` from uvicorn
- Use environment variables, not `.env` file
- Restrict CORS to specific domains
- Use a process manager (systemd, supervisor, etc.)
- Add authentication to `/api/chat`
- Use persistent storage for conversation history
- Deploy with proper logging and monitoring

## Support

For issues with:
- **MySQL**: Check DBRE agent configuration in `.env`
- **Claude API**: Verify API key and rate limits
- **Frontend**: Check browser console and network tab
- **Backend**: Check application logs and `/health` endpoint
