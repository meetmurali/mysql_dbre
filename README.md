# MySQL DBRE Agent 🛠️

An AI-powered MySQL Database Reliability Engineering (DBRE) assistant that lets you monitor and analyze your MySQL database health using natural language questions — running entirely on your local machine with no cloud API required.

---

## 🏗️ Architecture Overview

```
User (Browser)
     ↕
React + Vite Frontend
     ↕
FastAPI Backend  ←→  Ollama (Local LLM: llama3.2)
     ↕
MySQL Database
```

---

## ⚙️ Prerequisites

Install the following before proceeding:

| Software | Version | Download |
|---|---|---|
| Python | 3.11+ | https://python.org |
| Node.js + npm | 18+ | https://nodejs.org |
| Ollama | Latest | https://ollama.com/download |
| MySQL Server | 5.7+ or 8.0+ | https://dev.mysql.com/downloads |

---

## 🚀 Installation & Setup

### Step 1 — Clone the Repository
```bash
git clone https://github.com/meetmurali/MySQL_DBRE.git
cd MySQL_DBRE
```

### Step 2 — Install Ollama and Pull the LLM Model
```bash
# Download and install Ollama from https://ollama.com/download
# Then pull the required model:
ollama pull llama3.2
```

### Step 3 — Set Up Python Backend
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate        # Mac/Linux
# venv\Scripts\activate         # Windows

# Install Python dependencies
pip install -r requirements.txt
```

### Step 4 — Set Up the Frontend
```bash
cd frontend
npm install
cd ..
```

### Step 5 — Create the MySQL Read-Only User
Run this SQL script on your MySQL server to create the required `dbre_agent` user:
```bash
mysql -u root -p < setup_mysql_user.sql
```

### Step 6 — Configure Environment Variables
Create a `.env` file in the root directory:
```bash
cp .env.example .env
```
Then edit `.env` with your actual values:
```
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=dbre_agent
MYSQL_PASSWORD=your_password_here
MYSQL_DATABASE=your_database_name
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.2:latest
```

> ⚠️ Never commit your `.env` file to source control. It is already in `.gitignore`.

---

## ▶️ Running the Application

### Start the Backend
```bash
# Make sure your virtual environment is active
source venv/bin/activate
uvicorn backend.main:app --reload --port 8000
```

### Start the Frontend (in a new terminal)
```bash
cd frontend
npm run dev
```

### Open in Browser
```
http://localhost:5173
```

---

## 💬 Example Questions You Can Ask

- *"What is the current replication lag?"*
- *"Show me the top 20 active processes"*
- *"Are there any slow queries running?"*
- *"What is the server uptime?"*
- *"What is the replication topology?"*

---

## 🔒 Security & Safety

- **Read-only mode strictly enforced** — no writes, deletes, or schema changes possible
- **Non-blocking queries only** — zero performance impact on your database
- **30-second query timeout** — automatically aborts and alerts if a query hangs
- **Whitelisted queries only** — no arbitrary SQL execution
- **Least-privilege DB user** — `dbre_agent` has only SELECT, SHOW, PROCESS, REPLICATION CLIENT privileges

---

## 🔄 Switching LLM Models

You can use any Ollama-supported model. To switch:
```bash
# Pull a different model
ollama pull mistral
# or
ollama pull llama3.2

# Update your .env
OLLAMA_MODEL=mistral:latest
```

---

## 📁 Project Structure

```
MySQL_DBRE/
├── backend/
│   └── main.py          # FastAPI backend + tool orchestration
├── frontend/            # React + Vite UI
├── agent.py             # Agent logic + LLM client
├── database.py          # MySQL connection + query execution
├── queries.py           # Whitelisted SQL query templates
├── mcp_server.py        # Optional MCP server for Claude Code
├── example_usage.py     # Local testing harness
├── main.py              # Interactive CLI
├── setup_mysql_user.sql # SQL to create read-only DB user
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variable template
└── README.md            # This file
```

---

## 🤝 Contributing

Pull requests are welcome! Please ensure any new queries added follow the read-only and non-blocking guidelines in `queries.py`.