@echo off
chcp 65001 > nul
REM acestep.cpp 启动脚本 (CPU 版本)
REM GPU 版本编译完成后，替换为 build-cuda\

setlocal

set "SCRIPT_DIR=%~dp0"
set "BUILD_DIR=%SCRIPT_DIR%build-cpu"
set "MODELS_DIR=%SCRIPT_DIR%models"
if not defined ACE_HOST set "ACE_HOST=127.0.0.1"
if not defined ACE_PORT set "ACE_PORT=8085"

echo =====================================
echo   acestep.cpp server
echo   Build: CPU
echo   Models: %MODELS_DIR%
echo   Listen: %ACE_HOST%:%ACE_PORT%
echo =====================================
echo.

REM 检查模型文件
for %%f in (
  "vae-BF16.gguf"
  "Qwen3-Embedding-0.6B-Q8_0.gguf"
  "acestep-5Hz-lm-4B-Q5_K_M.gguf"
  "acestep-v15-turbo-Q4_K_M.gguf"
) do (
  if not exist "%MODELS_DIR%\%%~f" (
    echo ERROR: 缺少模型文件: %%~f
    exit /b 1
  )
  echo [OK] %%~f
)
echo.

echo Starting ace-server...
"%BUILD_DIR%\ace-server.exe" ^
  --models "%MODELS_DIR%" ^
  --host %ACE_HOST% ^
  --port %ACE_PORT% ^
  --vae-chunk 128 ^
  --vae-overlap 32
