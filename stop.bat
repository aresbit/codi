@echo off
chcp 65001 >nul
title Codi Stop Services
cd /d "%~dp0"
set "NO_PAUSE="
if /I "%~1"=="/nopause" set "NO_PAUSE=1"

echo ============================================
echo   Codi - Stop All Services
echo ============================================
echo.

echo [1/3] Stopping acestep engine...
taskkill /f /im ace-server.exe >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] acestep stopped
) else (
    echo [INFO] acestep was not running
)

echo [2/3] Stopping Backend (FastAPI)...
taskkill /f /fi "WINDOWTITLE eq codi-backend*" >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000 "') do (
    taskkill /f /pid %%a >nul 2>&1
)
echo [OK] Backend stopped

echo [3/3] Stopping Webapp (Vite)...
taskkill /f /fi "WINDOWTITLE eq codi-webapp*" >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5173 "') do (
    taskkill /f /pid %%a >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5174 "') do (
    taskkill /f /pid %%a >nul 2>&1
)
echo [OK] Webapp stopped

echo.
echo ============================================
echo   All services are stopped.
echo   Ports 8000, 8085, 5173, 5174 have been released.
echo ============================================
if not defined NO_PAUSE pause
