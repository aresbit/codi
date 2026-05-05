@echo off
chcp 65001 >nul
title Codi Launcher
cd /d "%~dp0"
set "NO_PAUSE="
if /I "%~1"=="/nopause" set "NO_PAUSE=1"

echo ============================================
echo   Codi - AI Music One-Click Start
echo ============================================
echo.

echo [1/5] Checking environment...

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python 3.10+
    if not defined NO_PAUSE pause
    exit /b 1
)

where npx >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js/npx not found. Please install Node.js 18+
    if not defined NO_PAUSE pause
    exit /b 1
)

if not exist "acestep\build-gpu\ace-server.exe" (
    if not exist "acestep\build-cpu\ace-server.exe" (
        echo [ERROR] ace-server.exe not found. Build acestep first.
        if not defined NO_PAUSE pause
        exit /b 1
    )
)

echo [OK] Environment check passed
echo.

echo [2/5] Starting acestep engine...
if exist "acestep\build-gpu\ace-server.exe" (
    set ACE_BUILD=build-gpu
    echo       Mode: GPU (CUDA)
) else (
    set ACE_BUILD=build-cpu
    echo       Mode: CPU
)

start "acestep" /min cmd /c "acestep\%ACE_BUILD%\ace-server.exe --models acestep\models --host 127.0.0.1 --port 8085 --vae-chunk 128 --vae-overlap 32"
echo       Waiting for acestep to be ready (about 10-30 seconds)...

set ACA_READY=
for /l %%i in (1,1,30) do (
    >nul 2>&1 curl -s http://127.0.0.1:8085/health && set ACA_READY=1 && goto :acestep_ready
    >nul 2>&1 python -c "import socket; s=socket.socket(); s.settimeout(2); s.connect(('127.0.0.1',8085)); s.close()" && set ACA_READY=1 && goto :acestep_ready
    timeout /t 1 /nobreak >nul
)
:acestep_ready
if defined ACA_READY (
    echo [OK] acestep is ready (port 8085)
) else (
    echo [WARN] acestep may not be fully started. Continuing...
)
echo.

echo [3/5] Starting Backend (FastAPI)...

if exist "backend\codi.db" (
    del "backend\codi.db"
    echo       Old database removed
)

start "codi-backend" cmd /c "cd /d backend && python -m uvicorn app:app --host 0.0.0.0 --port 8000"
echo       Waiting for Backend to be ready...

set BACKEND_READY=
for /l %%i in (1,1,20) do (
    >nul 2>&1 python -c "import socket; s=socket.socket(); s.settimeout(2); s.connect(('127.0.0.1',8000)); s.close()" && set BACKEND_READY=1 && goto :backend_ready
    timeout /t 1 /nobreak >nul
)
:backend_ready
if defined BACKEND_READY (
    echo [OK] Backend is ready (port 8000)
) else (
    echo [WARN] Backend may not be fully started
)
echo.

echo [4/5] Starting Webapp (Vite + React)...
start "codi-webapp" cmd /c "cd /d webapp && npx vite --host"

set WAIT_COUNT=0
:wait_webapp
set /a WAIT_COUNT+=1
if %WAIT_COUNT% gtr 20 (
    echo [INFO] Webapp is starting. Check the webapp console window.
    goto :done
)
>nul 2>&1 python -c "import socket; s=socket.socket(); s.settimeout(2); s.connect(('127.0.0.1',5173)); s.close()" && goto :webapp_5173
>nul 2>&1 python -c "import socket; s=socket.socket(); s.settimeout(2); s.connect(('127.0.0.1',5174)); s.close()" && set WEBAPP_PORT=5174 && goto :webapp_ready
timeout /t 1 /nobreak >nul
goto :wait_webapp

:webapp_5173
set WEBAPP_PORT=5173
goto :webapp_ready

:webapp_ready
echo [OK] Webapp is ready (port %WEBAPP_PORT%)
echo.

:done
echo ============================================
echo   Codi started successfully!
echo.
echo   Webapp:    http://localhost:%WEBAPP_PORT%
echo   Backend:   http://localhost:8000
echo   acestep:   http://127.0.0.1:8085
echo.
if not defined NO_PAUSE echo   Press any key to open Webapp (closing this window will NOT stop services)
echo ============================================
if not defined NO_PAUSE pause >nul

start http://localhost:%WEBAPP_PORT%
