#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND_DIR="$ROOT_DIR/frontend"
BACKEND_DIR="$ROOT_DIR"

FRONTEND_LOG="$ROOT_DIR/frontend.log"
BACKEND_LOG="$ROOT_DIR/backend.log"
FRONTEND_PID_FILE="$ROOT_DIR/frontend.pid"
BACKEND_PID_FILE="$ROOT_DIR/backend.pid"

start_backend() {
  echo "Starting backend..."
  if lsof -i :8000 -t >/dev/null 2>&1; then
    echo "Backend appears to be already running on port 8000"
    return
  fi
  pushd "$BACKEND_DIR" >/dev/null
  nohup python3 -m backend.main > "$BACKEND_LOG" 2>&1 &
  echo $! > "$BACKEND_PID_FILE"
  popd >/dev/null
  echo "Backend started (pid $(cat $BACKEND_PID_FILE)), logs: $BACKEND_LOG"
}

start_frontend() {
  echo "Starting frontend..."
  if lsof -i :5173 -t >/dev/null 2>&1; then
    echo "Frontend appears to be already running on port 5173"
    return
  fi
  pushd "$FRONTEND_DIR" >/dev/null
  # install dependencies if node_modules missing
  if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies (npm install)"
    npm install
  fi
  nohup npm run dev > "$FRONTEND_LOG" 2>&1 &
  echo $! > "$FRONTEND_PID_FILE"
  popd >/dev/null
  echo "Frontend started (pid $(cat $FRONTEND_PID_FILE)), logs: $FRONTEND_LOG"
}

stop_backend() {
  echo "Stopping backend..."
  if [ -f "$BACKEND_PID_FILE" ]; then
    kill "$(cat $BACKEND_PID_FILE)" || true
    rm -f "$BACKEND_PID_FILE"
    echo "Stopped backend"
  else
    pids=$(lsof -i :8000 -t || true)
    if [ -n "$pids" ]; then
      kill $pids || true
      echo "Killed backend pids: $pids"
    else
      echo "No backend process found"
    fi
  fi
}

stop_frontend() {
  echo "Stopping frontend..."
  if [ -f "$FRONTEND_PID_FILE" ]; then
    kill "$(cat $FRONTEND_PID_FILE)" || true
    rm -f "$FRONTEND_PID_FILE"
    echo "Stopped frontend"
  else
    pids=$(lsof -i :5173 -t || true)
    if [ -n "$pids" ]; then
      kill $pids || true
      echo "Killed frontend pids: $pids"
    else
      echo "No frontend process found"
    fi
  fi
}

status() {
  echo "Backend port 8000:"
  lsof -i :8000 -P -n || true
  echo
  echo "Frontend port 5173:"
  lsof -i :5173 -P -n || true
}

case "${1:-}" in
  start)
    start_backend
    start_frontend
    ;;
  start-backend)
    start_backend
    ;;
  start-frontend)
    start_frontend
    ;;
  stop)
    stop_frontend
    stop_backend
    ;;
  restart)
    stop
    start
    ;;
  status)
    status
    ;;
  *)
    echo "Usage: $0 {start|start-backend|start-frontend|stop|restart|status}"
    exit 1
    ;;
esac
