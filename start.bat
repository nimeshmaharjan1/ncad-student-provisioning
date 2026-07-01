@echo off
title NCAD Student Provisioning
cd /d "%~dp0"

echo ============================================
echo   NCAD Student Provisioning -- Launcher
echo ============================================
echo.
echo Checking prerequisites...
echo.

:: ----- Check Python ---------------------------------------------------------
echo [1/5] Checking Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not on PATH.
    echo Please install Python 3.10+ from https://python.org
    echo.
    pause
    exit /b 1
)

:: ----- Check pip ------------------------------------------------------------
echo [2/5] Checking pip...
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] pip is not installed.
    echo Python 3.4+ includes pip by default. Reinstall Python and make sure
    echo "Add Python to PATH" and "Install pip" are checked during setup.
    echo.
    pause
    exit /b 1
)

:: ----- Check Node.js ---------------------------------------------------------
echo [3/5] Checking Node.js...
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js is not installed or not on PATH.
    echo Please install Node.js 20+ from https://nodejs.org
    echo.
    pause
    exit /b 1
)

:: ----- Check npm ------------------------------------------------------------
echo [4/5] Checking npm...
call npm --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] npm is not installed.
    echo Node.js 20+ includes npm by default. Reinstall from https://nodejs.org
    echo.
    pause
    exit /b 1
)

:: ----- Check system ports ----------------------------------------------------
echo [5/5] Checking system ports...
:: Auto-kill orphaned processes on ports 8000 and 3000.
:: Uses netstat + taskkill (native cmd) instead of PowerShell,
:: because corporate Windows may restrict PowerShell execution policy.
for /f "tokens=5 delims= " %%p in ('netstat -ano ^| findstr ":8000"') do (
    if not "%%p"=="" taskkill /F /PID %%p >nul 2>&1 && echo [INFO] Port 8000 was in use - killed leftover process.
)
for /f "tokens=5 delims= " %%p in ('netstat -ano ^| findstr ":3000"') do (
    if not "%%p"=="" taskkill /F /PID %%p >nul 2>&1 && echo [INFO] Port 3000 was in use - killed leftover process.
)

echo.
echo All prerequisites met.
echo.

:: ----------------------------------------------------------------------------
:: Backend
:: ----------------------------------------------------------------------------
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

:: ----------------------------------------------------------------------------
:: Frontend
:: ----------------------------------------------------------------------------
echo [4/4] Setting up and starting frontend on http://localhost:3000 ...
cd frontend
call npm install
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install Node.js dependencies.
    pause
    exit /b 1
)
echo Building frontend for production ^(this may take a minute^)...
call npm run build
echo Build complete.
start /B "" cmd /c "npm run start"
cd ..

echo.
echo ============================================
echo   All servers starting...
echo   Backend:  http://localhost:8000
echo   Frontend: http://localhost:3000
echo ============================================
echo.

:: ----- Wait for frontend to be ready -----------------------------------------
:: Uses netstat (native cmd) instead of PowerShell to avoid corporate
:: execution policy restrictions on New-Object / Get-NetTCPConnection.
:: Polls every ~2 seconds for up to 120 seconds.
echo Waiting for frontend to start (this may take a minute)...
for /l %%i in (1,1,60) do (
    >nul 2>&1 netstat -ano | findstr ":3000" | findstr "LISTENING" && (
        echo Frontend ready.
        goto :frontend_up
    )
    >nul ping -n 3 localhost
)
echo [WARN] Frontend not ready after 120s. Open http://localhost:3000 manually.
:frontend_up

:: ----- Open browser ----------------------------------------------------------
start http://localhost:3000

echo.
echo Browser should open automatically.
echo Close this window to stop both servers.
echo.
pause
