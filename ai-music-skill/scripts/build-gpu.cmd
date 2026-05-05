@echo off
REM Build acestep.cpp with CUDA GPU support
REM Usage: build-gpu.cmd [source_dir]

set "SCRIPT_DIR=%~dp0"
if not "%~1"=="" (
    set "ACE_DIR=%~1"
) else (
    set "ACE_DIR=%CD%"
)

echo ===== acestep.cpp CUDA Build =====
echo Source: %ACE_DIR%

REM Set up MSVC environment (adjust path if needed)
call "D:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: vcvars64.bat not found
    echo Make sure MSVC Build Tools are installed.
    echo Try: call "%%ProgramFiles(x86)%%\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
    exit /b 1
)

REM Clean and rebuild
if exist build-gpu rmdir /s /q build-gpu
mkdir build-gpu
cd build-gpu

echo [1/2] Configuring with CMake (CUDA)...
cmake "%ACE_DIR%" ^
    -DGGML_CUDA=ON ^
    -DCMAKE_BUILD_TYPE=Release ^
    -DCMAKE_CUDA_ARCHITECTURES="86-real" ^
    -DCMAKE_CUDA_FLAGS="-allow-unsupported-compiler" ^
    -DGGML_CCACHE=OFF ^
    -G Ninja

if %ERRORLEVEL% NEQ 0 (
    echo CMake configuration FAILED!
    exit /b 1
)

echo [2/2] Building...
cmake --build . --config Release -j %NUMBER_OF_PROCESSORS%

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ===== Build SUCCESS! =====
    echo Binaries in: %CD%
    dir *.exe *.dll
) else (
    echo.
    echo ===== Build FAILED! =====
    exit /b 1
)

cd ..
