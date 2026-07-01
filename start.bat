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

:: Check pip (Python may be installed without it)
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] pip is not installed.
    echo Python 3.4+ includes pip by default. Reinstall Python and make sure
    echo "Add Python to PATH" and "Install pip" are checked during setup.
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

:: Check npm (Node may be installed without it)
npm --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] npm is not installed.
    echo Node.js 20+ includes npm by default. Reinstall from https://nodejs.org
    echo.
    pause
    exit /b 1
)

:: Auto-kill orphaned processes on ports 8000 and 3000.
:: This handles the case where a previous terminal was closed but
:: the Node / uvicorn process kept running (orphaned). Non-IT users
:: don't need to hunt down PIDs — the script just cleans up.
:: If you intentionally have something else on these ports, kill it manually.
powershell -NoProfile -Command "Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue; Write-Host '[INFO] Port 8000 was in use - killed leftover process.' }"
powershell -NoProfile -Command "Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue; Write-Host '[INFO] Port 3000 was in use - killed leftover process.' }"

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

:: Wait for frontend to be ready (poll port 3000, max 120 seconds)
echo Waiting for frontend to start (this may take a minute)...
powershell -NoProfile -Command ^
  "$t = [datetime]::Now.AddSeconds(120); ^
   while (1) { ^
     try { ^
       $c = New-Object Net.Sockets.TcpClient('127.0.0.1', 3000); ^
       $c.Close(); ^
       Write-Host 'Frontend ready.'; ^
       break ^
     } catch { ^
       Start-Sleep -Seconds 2 ^
     } ^
     if ([datetime]::Now -ge $t) { ^
       Write-Host '[WARN] Frontend not ready after 120s. Open http://localhost:3000 manually.'; ^
       break ^
     } ^
   }"

:: Open browser
start http://localhost:3000

echo.
echo Browser should open automatically.
echo Close this window to stop both servers.
echo.
pause
