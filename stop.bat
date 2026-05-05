@echo off
chcp 65001 >nul
title Codi 停止服务
cd /d "%~dp0"

echo ============================================
echo   Codi — 停止所有服务
echo ============================================
echo.

:: ========== 1. 停止 acestep ==========
echo [1/3] 停止 acestep 音乐引擎...
taskkill /f /im ace-server.exe >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] acestep 已停止
) else (
    echo [信息] acestep 未运行
)

:: ========== 2. 停止 Backend ==========
echo [2/3] 停止 Backend (FastAPI)...
taskkill /f /fi "WINDOWTITLE eq codi-backend*" >nul 2>&1

:: 也杀掉占用 8000 端口的 python 进程（Backend）
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000 "') do (
    taskkill /f /pid %%a >nul 2>&1
)
echo [OK] Backend 已停止

:: ========== 3. 停止 Webapp ==========
echo [3/3] 停止 Webapp (Vite)...

:: 通过窗口标题停止
taskkill /f /fi "WINDOWTITLE eq codi-webapp*" >nul 2>&1

:: 也杀掉占用 5173/5174 端口的 node 进程
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5173 "') do (
    taskkill /f /pid %%a >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5174 "') do (
    taskkill /f /pid %%a >nul 2>&1
)
echo [OK] Webapp 已停止

echo.
echo ============================================
echo   所有服务已停止！
echo   端口 8000, 8085, 5173, 5174 已释放。
echo ============================================
pause
