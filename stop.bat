@echo off
cd /d "%~dp0"

:: 使用 PowerShell 输出中文（避免 cmd.exe 编码问题）
set "PWS=powershell -NoProfile -Command Write-Host"

%PWS% "============================================" -ForegroundColor Cyan
%PWS% "  Codi - 停止所有服务" -ForegroundColor Cyan
%PWS% "============================================" -ForegroundColor Cyan
echo.

:: ========== 1. 停止 acestep ==========
%PWS% "[1/3] 停止 acestep 音乐引擎..." -ForegroundColor Yellow
taskkill /f /im ace-server.exe >nul 2>&1
if %errorlevel% equ 0 (
    %PWS% "[OK] acestep 已停止" -ForegroundColor Green
) else (
    %PWS% "[信息] acestep 未运行" -ForegroundColor Gray
)

:: ========== 2. 停止 Backend ==========
%PWS% "[2/3] 停止 Backend (FastAPI)..." -ForegroundColor Yellow
taskkill /f /fi "WINDOWTITLE eq codi-backend*" >nul 2>&1

:: 也杀掉占用 8000 端口的 python 进程（Backend）
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000 "') do (
    taskkill /f /pid %%a >nul 2>&1
)
%PWS% "[OK] Backend 已停止" -ForegroundColor Green

:: ========== 3. 停止 Webapp ==========
%PWS% "[3/3] 停止 Webapp (Vite)..." -ForegroundColor Yellow

:: 通过窗口标题停止
taskkill /f /fi "WINDOWTITLE eq codi-webapp*" >nul 2>&1

:: 也杀掉占用 5173/5174 端口的 node 进程
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5173 "') do (
    taskkill /f /pid %%a >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5174 "') do (
    taskkill /f /pid %%a >nul 2>&1
)
%PWS% "[OK] Webapp 已停止" -ForegroundColor Green

echo.
%PWS% "============================================" -ForegroundColor Cyan
%PWS% "  所有服务已停止!" -ForegroundColor Cyan
%PWS% "  端口 8000, 8085, 5173, 5174 已释放。" -ForegroundColor White
%PWS% "============================================" -ForegroundColor Cyan
pause
