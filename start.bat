@echo off
cd /d "%~dp0"

:: 使用 PowerShell 输出中文（避免 cmd.exe 编码问题）
set "PWS=powershell -NoProfile -Command Write-Host"

%PWS% "============================================" -ForegroundColor Cyan
%PWS% "  Codi - AI 音乐定制 一键启动" -ForegroundColor Cyan
%PWS% "============================================" -ForegroundColor Cyan
echo.

:: ========== 检查依赖 ==========
%PWS% "[1/5] 检查环境..." -ForegroundColor Yellow

where python >nul 2>&1
if %errorlevel% neq 0 (
    %PWS% "[错误] 未找到 Python，请安装 Python 3.10+" -ForegroundColor Red
    pause
    exit /b 1
)

where npx >nul 2>&1
if %errorlevel% neq 0 (
    %PWS% "[错误] 未找到 Node.js/npx，请安装 Node.js 18+" -ForegroundColor Red
    pause
    exit /b 1
)

:: 检查 ace-server.exe
if not exist "acestep\build-gpu\ace-server.exe" (
    if not exist "acestep\build-cpu\ace-server.exe" (
        %PWS% "[错误] 未找到 ace-server.exe，请先编译 acestep" -ForegroundColor Red
        pause
        exit /b 1
    )
)

%PWS% "[OK] 环境检查通过" -ForegroundColor Green
echo.

:: ========== 启动 acestep ==========
%PWS% "[2/5] 启动 acestep 音乐引擎..." -ForegroundColor Yellow
if exist "acestep\build-gpu\ace-server.exe" (
    set ACE_BUILD=build-gpu
    %PWS% "      模式: GPU (CUDA)" -ForegroundColor Green
) else (
    set ACE_BUILD=build-cpu
    %PWS% "      模式: CPU" -ForegroundColor Green
)

start "acestep" /min cmd /c "acestep\start-server.sh" 2>nul
if %errorlevel% neq 0 (
    start "acestep" /min cmd /c "acestep\%ACE_BUILD%\ace-server.exe --models acestep\models --host 127.0.0.1 --port 8085 --vae-chunk 128 --vae-overlap 32"
)
%PWS% "      等待 acestep 就绪(约 10-30 秒)..." -ForegroundColor Gray

:: 等待 acestep 就绪
set ACA_READY=
for /l %%i in (1,1,30) do (
    >nul 2>&1 curl -s http://127.0.0.1:8085/health && set ACA_READY=1 && goto :acestep_ready
    >nul 2>&1 python -c "import socket; s=socket.socket(); s.settimeout(2); s.connect(('127.0.0.1',8085)); s.close()" && set ACA_READY=1 && goto :acestep_ready
    timeout /t 1 /nobreak >nul
)
:acestep_ready
if defined ACA_READY (
    %PWS% "[OK] acestep 已就绪(端口 8085)" -ForegroundColor Green
) else (
    %PWS% "[警告] acestep 可能未完全启动，将继续启动其他服务" -ForegroundColor Yellow
)
echo.

:: ========== 启动 Backend ==========
%PWS% "[3/5] 启动 Backend (FastAPI)..." -ForegroundColor Yellow

:: 删除旧数据库（schema 变更时需重建）
if exist "backend\codi.db" (
    del "backend\codi.db"
    %PWS% "      已清理旧数据库" -ForegroundColor Gray
)

start "codi-backend" cmd /c "cd /d backend && python -m uvicorn app:app --host 0.0.0.0 --port 8000"
%PWS% "      等待 Backend 就绪..." -ForegroundColor Gray

set BACKEND_READY=
for /l %%i in (1,1,20) do (
    >nul 2>&1 python -c "import socket; s=socket.socket(); s.settimeout(2); s.connect(('127.0.0.1',8000)); s.close()" && set BACKEND_READY=1 && goto :backend_ready
    timeout /t 1 /nobreak >nul
)
:backend_ready
if defined BACKEND_READY (
    %PWS% "[OK] Backend 已就绪(端口 8000)" -ForegroundColor Green
) else (
    %PWS% "[警告] Backend 可能未完全启动" -ForegroundColor Yellow
)
echo.

:: ========== 启动 Webapp ==========
%PWS% "[4/5] 启动 Webapp (Vite + React)..." -ForegroundColor Yellow
start "codi-webapp" cmd /c "cd /d webapp && npx vite --host"

:: 等待 webapp 就绪
set WAIT_COUNT=0
:wait_webapp
set /a WAIT_COUNT+=1
if %WAIT_COUNT% gtr 20 (
    %PWS% "[信息] Webapp 启动中，请稍候查看控制台窗口" -ForegroundColor Gray
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
%PWS% "[OK] Webapp 已就绪(端口 %WEBAPP_PORT%)" -ForegroundColor Green
echo.

:: ========== 完成 ==========
:done
%PWS% "============================================" -ForegroundColor Cyan
%PWS% "  Codi 启动完成!" -ForegroundColor Cyan
%PWS% "" -ForegroundColor Cyan
%PWS% "  Webapp:    http://localhost:%WEBAPP_PORT%" -ForegroundColor White
%PWS% "  Backend:   http://localhost:8000" -ForegroundColor White
%PWS% "  acestep:   http://127.0.0.1:8085" -ForegroundColor White
%PWS% "" -ForegroundColor Cyan
%PWS% "  按任意键打开 Webapp(关闭本窗口不会关闭服务)" -ForegroundColor Cyan
%PWS% "============================================" -ForegroundColor Cyan
pause >nul

:: 打开浏览器
start http://localhost:%WEBAPP_PORT%
