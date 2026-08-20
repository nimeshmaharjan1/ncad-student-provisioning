@echo off
title NCAD Student Provisioning
set "_DIR=%~dp0"
if "%_DIR:~0,2%"=="\\" (
    echo [ERROR] You are running this from a shared/network drive.
    echo Copy the folder to your own machine first, then run start.bat there.
    echo.
    pause
    exit /b 1
)
cd /d "%~dp0"
:: .venv\Scripts\python -m uvicorn app.main:app --reload --port 8000
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
for /f "tokens=5 delims= " %%p in ('netstat -ano ^| findstr ":8000" ^| findstr "LISTENING"') do (
    if not "%%p"=="" taskkill /F /PID %%p >nul 2>&1 && echo [INFO] Port 8000 was in use (PID %%p) - killed leftover process.
)
for /f "tokens=5 delims= " %%p in ('netstat -ano ^| findstr ":3000" ^| findstr "LISTENING"') do (
    if not "%%p"=="" taskkill /F /PID %%p >nul 2>&1 && echo [INFO] Port 3000 was in use (PID %%p) - killed leftover process.
)

echo.
echo All prerequisites met.
echo.

:: ----- Run the self-healing setup --------------------------------------------
:: Creates/repairs venv, deps, words.txt check, node_modules, build.
echo Running self-healing setup...
python scripts\bootstrap.py
if %errorlevel% neq 0 (
    echo [ERROR] Setup failed. See messages above.
    pause
    exit /b 1
)
echo.

:: ----------------------------------------------------------------------------
:: Backend
:: ----------------------------------------------------------------------------
echo [1/2] Starting backend on http://localhost:8000 ...
cd backend
start /B "" cmd /c ".venv\Scripts\python -m uvicorn app.main:app --port 8000"
cd ..

:: ----------------------------------------------------------------------------
:: Frontend
:: ----------------------------------------------------------------------------
echo [2/2] Starting frontend on http://localhost:3000 ...
cd frontend
start /B "" cmd /c "npm run start"
cd ..

echo.
echo ============================================
echo   All servers starting...
echo   Backend:  http://localhost:8000
echo   Frontend: http://localhost:3000
echo   Docs:     http://localhost:3000/about
echo ============================================
echo.

:: ----- Wait for frontend to be ready -----------------------------------------
:: Uses netstat (native cmd) instead of PowerShell to avoid corporate
:: execution policy restrictions on New-Object / Get-NetTCPConnection.
:: NOTE: the ">nul 2>&1" must come AFTER the pipe chain - if placed before
:: netstat it swallows netstat's output and the check never matches.
echo Waiting for frontend to start...
for /l %%i in (1,1,15) do (
    netstat -ano | findstr ":3000" | findstr "LISTENING" >nul 2>&1 && (
        echo Frontend ready.
        goto :frontend_up
    )
    >nul ping -n 2 localhost
)
echo [WARN] Frontend did not become ready after ~15 seconds.
echo        It may still be starting - open http://localhost:3000 manually.
:frontend_up

:: ----- Check backend is listening ---------------------------------------------
echo Checking backend on port 8000...
for /l %%i in (1,1,8) do (
    netstat -ano | findstr ":8000" | findstr "LISTENING" >nul 2>&1 && (
        echo Backend ready.
        goto :backend_up
    )
    >nul ping -n 2 localhost
)
echo [WARN] Backend did not become ready after ~8 seconds.
echo        Look for an error in the window above and retry - the frontend
echo        will not work without it.
:backend_up

:: ----- Open browser tabs -----------------------------------------------------
start http://localhost:3000
start http://localhost:3000/about

echo.
echo ============================================
echo   Servers are running.
echo   Backend:  http://localhost:8000
echo   Frontend: http://localhost:3000
echo   Docs:     http://localhost:3000/about
echo.
echo   This window stays open while the servers run.
echo   To stop them, close this window (X) or press Ctrl+C.
echo ============================================
