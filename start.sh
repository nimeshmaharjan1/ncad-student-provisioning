#!/usr/bin/env bash
# HOW TO RUN ON macOS/LINUX (nothing else needed):
#
#   Option A - no permissions to change:   bash start.sh
#   Option B - one-time, then ./start.sh:  chmod +x start.sh  &&  ./start.sh
#
# The script self-heals the venv, deps, words.txt, node_modules and
# frontend build, then starts backend (:8000) + frontend (:3000).
# Press Ctrl+C to stop.
#
# If double-clicking or ./start.sh ever says "Permission denied", the file
# lost its executable bit - run  chmod +x start.sh  once. Fresh clones of
# this repo already have it set. If double-clicking opens an editor instead
# of running, use  bash start.sh  (or right-click > Open With > Terminal).

cd "$(dirname "$0")"

case "$(pwd)" in
  /Volumes/*|/mnt/*|/media/*)
    echo "[ERROR] You are running this from a shared/network drive."
    echo "Copy the folder to your own machine first, then run start.sh there."
    exit 1
    ;;
esac

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

# Wait a moment for the OS to fully free the ports before starting.
echo "Waiting for ports to free..."
for i in 1 2 3 4 5; do
  if ! lsof -ti:8000 >/dev/null 2>&1; then break; fi
  sleep 1
done
if lsof -ti:8000 >/dev/null 2>&1; then
  echo "[WARN] Port 8000 still busy after 5s - try: lsof -ti:8000 | xargs kill -9"
fi
for i in 1 2 3 4 5; do
  if ! lsof -ti:3000 >/dev/null 2>&1; then break; fi
  sleep 1
done
if lsof -ti:3000 >/dev/null 2>&1; then
  echo "[WARN] Port 3000 still busy after 5s - try: lsof -ti:3000 | xargs kill -9"
fi

cleanup() {
  echo ""
  echo "Shutting down..."
  [ -n "$BACKEND_PID" ] && kill "$BACKEND_PID" 2>/dev/null
  [ -n "$FRONTEND_PID" ] && kill "$FRONTEND_PID" 2>/dev/null
  exit
}
trap cleanup INT TERM

# Run the self-healing setup (venv, deps, words.txt, node_modules, build)
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

# Wait for frontend to be ready (poll port 3000, up to ~4 minutes; first
# start is slow). Tries curl first, then wget, then nc — not all systems
# have curl.
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
  echo "Waiting for frontend to start (first start can take a couple of minutes)..."
  for i in $(seq 1 240); do
    if $CHECK_CMD 2>/dev/null; then
      echo "Frontend ready."
      break
    fi
    sleep 1
  done
  if ! $CHECK_CMD 2>/dev/null; then
    echo "[WARN] Frontend not ready after ~4 minutes. It may still be starting -"
    echo "       open http://localhost:3000 manually."
  fi
else
  echo "[WARN] curl, wget, nc not found — cannot verify frontend is ready."
  echo "If the browser doesn't open, visit http://localhost:3000 manually."
fi

echo ""
echo "Open these links (Ctrl/Cmd+Click):"
echo "  Backend:  http://localhost:8000"
echo "  Frontend: http://localhost:3000"
echo "  Docs:     http://localhost:3000/about"
echo "Press Ctrl+C to stop both servers."
echo ""

wait
