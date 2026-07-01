#!/usr/bin/env bash

cd "$(dirname "$0")"

echo "============================================"
echo "  NCAD Student Provisioning -- Launcher"
echo "============================================"
echo ""

# Check Python
PYTHON=""
if command -v python3 &>/dev/null; then
  PYTHON="python3"
elif command -v python &>/dev/null; then
  PYTHON="python"
else
  echo "[ERROR] Python is not installed."
  echo "Please install Python 3.10+ from https://python.org"
  exit 1
fi

# Check pip (Python may be installed without it)
if ! "$PYTHON" -m pip --version &>/dev/null; then
  echo "[ERROR] pip is not installed."
  echo "Python 3.4+ includes pip by default. Reinstall Python or install pip manually."
  exit 1
fi

# Check Node
if ! command -v node &>/dev/null; then
  echo "[ERROR] Node.js is not installed."
  echo "Please install Node.js 20+ from https://nodejs.org"
  exit 1
fi

# Check npm (Node may be installed without it)
if ! command -v npm &>/dev/null; then
  echo "[ERROR] npm is not installed."
  echo "Node.js 20+ includes npm by default. Reinstall from https://nodejs.org"
  exit 1
fi

# Auto-kill orphaned processes on ports 8000 and 3000.
# Tries lsof first, then fuser — covers both macOS and Linux.
kill_port() {
  local port=$1
  local pid=""
  if command -v lsof &>/dev/null; then
    pid=$(lsof -ti:"$port" 2>/dev/null)
  elif command -v fuser &>/dev/null; then
    pid=$(fuser "$port/tcp" 2>/dev/null | awk '{print $1}')
  fi
  if [ -n "$pid" ]; then
    kill -9 "$pid" 2>/dev/null
    echo "[INFO] Port $port was in use - killed leftover process."
  fi
}
kill_port 8000
kill_port 3000

cleanup() {
  echo ""
  echo "Shutting down..."
  [ -n "$BACKEND_PID" ] && kill "$BACKEND_PID" 2>/dev/null
  [ -n "$FRONTEND_PID" ] && kill "$FRONTEND_PID" 2>/dev/null
  exit
}
trap cleanup INT TERM

# ------------------------------------------------------------------
# Backend
# ------------------------------------------------------------------
echo "[1/4] Setting up Python virtual environment..."
cd backend
if [ ! -d ".venv" ]; then
  "$PYTHON" -m venv .venv
fi
echo ""

echo "[2/4] Installing Python dependencies..."
.venv/bin/python -m pip install -r ../requirements.txt
if [ $? -ne 0 ]; then
  echo "[ERROR] Failed to install Python dependencies."
  exit 1
fi
echo ""

echo "[3/4] Starting backend on http://localhost:8000 ..."
.venv/bin/python -m uvicorn app.main:app --port 8000 &
BACKEND_PID=$!
cd ..

# ------------------------------------------------------------------
# Frontend
# ------------------------------------------------------------------
echo "[4/4] Setting up and starting frontend on http://localhost:3000 ..."
cd frontend
npm install
if [ $? -ne 0 ]; then
  echo "[ERROR] Failed to install Node.js dependencies."
  exit 1
fi
echo "Building frontend for production (this may take a minute)..."
npm run build
echo "Build complete."
npm run start &
FRONTEND_PID=$!
cd ..

echo ""
echo "============================================"
echo "  All servers starting..."
echo "  Backend:  http://localhost:8000"
echo "  Frontend: http://localhost:3000"
echo "============================================"
echo ""

# Wait for frontend to be ready (poll port 3000, max 120 seconds).
# Tries curl first, then wget, then nc — not all systems have curl.
if command -v curl &>/dev/null; then
  CHECK_CMD="curl -s -o /dev/null http://localhost:3000"
elif command -v wget &>/dev/null; then
  CHECK_CMD="wget -q -O /dev/null http://localhost:3000"
elif command -v nc &>/dev/null; then
  CHECK_CMD="nc -z localhost 3000"
else
  CHECK_CMD=""
fi

if [ -n "$CHECK_CMD" ]; then
  echo "Waiting for frontend to start (this may take a minute)..."
  for i in $(seq 1 120); do
    if $CHECK_CMD 2>/dev/null; then
      echo "Frontend ready."
      break
    fi
    sleep 1
  done
else
  echo "[WARN] curl, wget, nc not found — cannot verify frontend is ready."
  echo "If the browser doesn't open, visit http://localhost:3000 manually."
fi

# Open browser
if command -v xdg-open &>/dev/null; then
  xdg-open http://localhost:3000
elif command -v open &>/dev/null; then
  open http://localhost:3000
fi

echo ""
echo "Browser should open automatically."
echo "Press Ctrl+C to stop both servers."
echo ""

wait
