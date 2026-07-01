@echo off
title NCAD Student Provisioning
cd /d "%~dp0"

echo ============================================
echo   NCAD Student Provisioning -- Launcher
echo ============================================
echo.

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not on PATH.
    echo Please install Python 3.10+ from https://python.org
    echo.
    pause
    exit /b 1
)

:: Check Node
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js is not installed or not on PATH.
    echo Please install Node.js 20+ from https://nodejs.org
    echo.
    pause
    exit /b 1
)

:: Kill any existing servers on the same ports
netstat -ano | findstr ":8000 " > .ports.txt
for /f "tokens=5" %%a in (.ports.txt) do taskkill /f /pid %%a >nul 2>&1
netstat -ano | findstr ":3000 " > .ports.txt
for /f "tokens=5" %%a in (.ports.txt) do taskkill /f /pid %%a >nul 2>&1
del .ports.txt 2>nul

:: ------------------------------------------------------------------
:: Backend
:: ------------------------------------------------------------------
echo [1/4] Setting up Python virtual environment...
cd backend
if not exist ".venv" (
    python -m venv .venv
)
echo.

echo [2/4] Installing Python dependencies...
.venv\Scripts\python -m pip install -r ..\requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install Python dependencies.
    pause
    exit /b 1
)
echo.

echo [3/4] Starting backend on http://localhost:8000 ...
start /B "" cmd /c ".venv\Scripts\python -m uvicorn app.main:app --port 8000"
cd ..

:: ------------------------------------------------------------------
:: Frontend
:: ------------------------------------------------------------------
echo [4/4] Setting up and starting frontend on http://localhost:3000 ...
cd frontend
call npm install
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install Node.js dependencies.
    pause
    exit /b 1
)
if not exist ".next" (
    echo Building frontend for production ^(this may take a minute^)...
    call npm run build
    echo Build complete.
)
start /B "" cmd /c "npm run start"
cd ..

echo.
echo ============================================
echo   All servers starting...
echo   Backend:  http://localhost:8000
echo   Frontend: http://localhost:3000
echo ============================================
echo.

timeout /t 5 /nobreak >nul

:: Open browser
start http://localhost:3000

echo.
echo Browser should open automatically.
echo Close this window to stop both servers.
echo.
pause
