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

# Check Node
if ! command -v node &>/dev/null; then
  echo "[ERROR] Node.js is not installed."
  echo "Please install Node.js 20+ from https://nodejs.org"
  exit 1
fi

# Check ports
if command -v lsof &>/dev/null; then
  if lsof -ti:8000 &>/dev/null; then
    echo "[WARN] Port 8000 is already in use."
    echo "       Close the other server first, then try again."
    exit 1
  fi
  if lsof -ti:3000 &>/dev/null; then
    echo "[WARN] Port 3000 is already in use."
    echo "       Close the other server first, then try again."
    exit 1
  fi
fi

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
.venv/bin/python -m uvicorn app.main:app --reload --port 8000 &
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
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "============================================"
echo "  All servers starting..."
echo "  Backend:  http://localhost:8000"
echo "  Frontend: http://localhost:3000"
echo "============================================"
echo ""

sleep 5

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
