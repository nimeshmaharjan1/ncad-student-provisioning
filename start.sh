#!/usr/bin/env bash
# HOW TO RUN ON macOS/LINUX (nothing else needed):
#
#   Option A - no permissions to change:   bash start.sh
#   Option B - one-time, then ./start.sh:  chmod +x start.sh  &&  ./start.sh
#
# The script self-heals the venv, deps, words.txt, node_modules, .env and
# frontend build, then starts backend (:8000) + frontend (:3000).
# Press Ctrl+C to stop.
#
# If double-clicking or ./start.sh ever says "Permission denied", the file
# lost its executable bit - run  chmod +x start.sh  once. Fresh clones of
# this repo already have it set. If double-clicking opens an editor instead
# of running, use  bash start.sh  (or right-click > Open With > Terminal).

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
    kill -9 $pid 2>/dev/null
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

# Run the self-healing setup (venv, deps, words.txt, node_modules, .env, build)
echo "Running self-healing setup..."
if ! "$PYTHON" scripts/bootstrap.py; then
  echo "[ERROR] Setup failed. See messages above."
  exit 1
fi
echo ""

# ------------------------------------------------------------------
# Backend
# ------------------------------------------------------------------
echo "[1/2] Starting backend on http://localhost:8000 ..."
cd backend
.venv/bin/python -m uvicorn app.main:app --port 8000 &
BACKEND_PID=$!
cd ..

# ------------------------------------------------------------------
# Frontend
# ------------------------------------------------------------------
echo "[2/2] Starting frontend on http://localhost:3000 ..."
cd frontend
npm run start &
FRONTEND_PID=$!
cd ..

echo ""
echo "============================================"
echo "  All servers starting..."
echo "  Backend:  http://localhost:8000"
echo "  Frontend: http://localhost:3000"
echo "  Docs:     http://localhost:3000/about"
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

# Open app and docs
if command -v xdg-open &>/dev/null; then
  xdg-open "http://localhost:3000"
  xdg-open "http://localhost:3000/about"
elif command -v open &>/dev/null; then
  open "http://localhost:3000"
  open "http://localhost:3000/about"
fi

echo ""
echo "Browser tabs should open automatically."
echo "Press Ctrl+C to stop both servers."
echo ""

wait
