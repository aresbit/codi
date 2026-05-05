# Build Guide — acestep.cpp GPU (CUDA)

## Required Tools

| Tool | Version | Purpose |
|------|---------|---------|
| MSVC Build Tools | 2022+ (v14.50) | Windows C++ compiler (CUDA requires MSVC on Windows) |
| CUDA Toolkit | 12.8+ | GPU compute backend |
| CMake | 4.x | Build system generator |
| Ninja | any | Fast build executor |

## Known Issues

### MSVC Version Too New for CUDA

CUDA 12.8 supports MSVC up to VS 2022 (~v14.3x). Newer MSVC (VS 2026 v14.50) triggers a fatal error in `host_config.h`:

```
fatal error C1189: #error: -- unsupported Microsoft Visual Studio version!
```

**Fix**: Add `-allow-unsupported-compiler` to CUDA flags:

```cmake
-DCMAKE_CUDA_FLAGS="-allow-unsupported-compiler"
```

### vcvars64.bat Path

The script `buildcuda.cmd` assumes MSVC at:
```
C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat
```

If installed to a custom path (e.g., `D:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\`), update the path accordingly.

## CUDA Architecture Selection

Set `-DCMAKE_CUDA_ARCHITECTURES` based on GPU:

| GPU | SM Version | Flag |
|-----|-----------|------|
| RTX 3060 Ti / RTX 3070 / RTX 3080 | SM 86 (Ampere) | `"86-real"` |
| RTX 4090 | SM 89 (Ada) | `"89-real"` |
| RTX 5090 | SM 120 (Blackwell) | `"120a-real"` |
| Multiple GPUs | Various | `"75-virtual;80-virtual;86-real;89-real"` |

- Use `-real` for your actual GPU (compiles fully), `-virtual` for JIT.
- `86-real` covers RTX 3060 Ti (Ampere architecture).

## Build Process (Windows)

```batch
call "path\to\vcvars64.bat"
mkdir build-gpu && cd build-gpu
cmake .. -DGGML_CUDA=ON ^
    -DCMAKE_BUILD_TYPE=Release ^
    -DCMAKE_CUDA_ARCHITECTURES="86-real" ^
    -DCMAKE_CUDA_FLAGS="-allow-unsupported-compiler" ^
    -DGGML_CCACHE=OFF ^
    -G Ninja
cmake --build . --config Release -j %NUMBER_OF_PROCESSORS%
```

## Build Output

| File | Size | Purpose |
|------|------|---------|
| `ace-server.exe` | ~1.3 MB | HTTP server for music generation |
| `ace-lm.exe` | ~400 KB | CLI: LM-based lyrics + params generation |
| `ace-synth.exe` | ~580 KB | CLI: audio synthesis |
| `ace-understand.exe` | ~420 KB | CLI: audio understanding |
| `ggml-cuda.dll` | ~30 MB | CUDA backend (GPU runtime) |
| `ggml-cpu.dll` | ~800 KB | CPU fallback backend |
| `ggml.dll` | ~70 KB | Core ggml library |

## Verification

After building, verify CUDA backend loads:
```bash
ace-server.exe --models ../models --host 127.0.0.1 --port 8085
```
Look for log messages confirming model registration. No errors means CUDA is working.
