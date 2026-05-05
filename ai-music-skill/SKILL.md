---
name: ai-music-skill
description: "Deploy, compile, and operate acestep.cpp for local GPU-accelerated AI music generation, plus full-stack Codi webapp deployment. Use when: (1) Building/compiling ace-server with CUDA support on Windows, (2) Selecting appropriate models for GPUs with 8GB VRAM, (3) Starting ace-server and generating songs via HTTP API, (4) Troubleshooting build issues (MSVC/CUDA version conflicts), (5) Writing song generation prompts for the 5Hz LM model, (6) Running the complete Codi webapp (FastAPI backend + Vite frontend + SQLite), (7) Open-sourcing or modifying the Codi app (removing payment/sheet music, adding MP3/MP4 downloads). Covers end-to-end workflow from engine compilation through full-stack web deployment."
---

# AI Music Generation — acestep.cpp GPU

Compile, deploy, and run ace-server with CUDA acceleration for local AI music synthesis.

## Quick Start

### 1. Compile GPU Version

```batch
call "D:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
mkdir build-gpu && cd build-gpu
cmake .. -DGGML_CUDA=ON -DCMAKE_BUILD_TYPE=Release -DCMAKE_CUDA_ARCHITECTURES="86-real" -DCMAKE_CUDA_FLAGS="-allow-unsupported-compiler" -DGGML_CCACHE=OFF -G Ninja
cmake --build . --config Release -j %NUMBER_OF_PROCESSORS%
```

Or run the bundled script:
```bash
scripts/build-gpu.cmd [path/to/acestep.cpp/source]
```

Detailed build environment info in [references/build-guide.md](references/build-guide.md).

### 2. Start Server

```batch
ace-server.exe --models ../models --host 127.0.0.1 --port 8085 --vae-chunk 128 --vae-overlap 32
```

Server listens on port 8085. Verify with `curl http://127.0.0.1:8085/health`.

### 3. Generate a Song

```bash
python scripts/test_generation.py --caption folk --output ./my_song
```

Or use custom prompts:
```bash
python scripts/test_generation.py --caption custom --custom-text "Style: ..." --output ./custom_song
```

Full API reference in [references/api-guide.md](references/api-guide.md).

## Model Selection (8GB VRAM)

For RTX 3060 Ti (8GB), use these quantized models (total ~5.5GB):

| Component | Model File | Size |
|-----------|-----------|------|
| LM | `acestep-5Hz-lm-4B-Q5_K_M.gguf` | 3.0 GB |
| DiT/Synth | `acestep-v15-turbo-Q4_K_M.gguf` | 1.4 GB |
| VAE | `vae-BF16.gguf` | 337 MB |
| Text Enc | `Qwen3-Embedding-0.6B-Q8_0.gguf` | 784 MB |

Detailed model guidance and param tuning in [references/model-guide.md](references/model-guide.md).

## Inference Parameters (8GB Optimized)

- `inference_steps`: 8 (turbo model, fewer steps = faster)
- `guidance_scale`: 1.0 (no guidance, default for turbo)
- `shift`: 3.0 (turbo flow-matching shift)
- `duration`: 180 (seconds, ~3 min)
- `vae-chunk`: 128 (process in chunks to save VRAM)
- `vae-overlap`: 32 (chunk overlap)

## Generation Workflow

### Two-Phase API Flow

```
Phase 1 (LM):  POST /lm → get job_id → poll GET /job?id=X → done → GET /job?id=X&result=1 → enriched JSON
Phase 2 (Synth): POST /synth (body=enriched JSON) → poll → done → GET /job?result=1 → MP3 binary
```

### Prompt Structure

Write captions with: **style description + theme + language + song structure**:
```
Style: [genre, instruments, vocal type, mood]
Theme: [1-2 sentence theme]
Language: Chinese
Structure: intro → verse → chorus → verse → chorus → bridge → chorus → outro
```

### LM Model Behavior

Read [references/lm-notes.md](references/lm-notes.md) for details. Key behavior:
- Chinese output is **pinyin with tone numbers** (phoneme tokenization), not Chinese characters
- English output is plain text
- Model mixes `[zh]` and `[en]` tags per line
- Cannot exactly reproduce user-provided lyrics — generates original content

## Parameter Tuning

- **Quality vs Speed**: Increase `inference_steps` to 24-50 for better quality (slower, more VRAM)
- **Prompt Adherence**: Increase `guidance_scale` to 3.0-7.0 (risk of audio distortion)
- **Song Length**: Adjust `duration` (longer = more VRAM)
- **VRAM Saving**: Lower `vae-chunk`, enable `vae-overlap`

## Troubleshooting

**MSVC version too new for CUDA**: Add `-DCMAKE_CUDA_FLAGS="-allow-unsupported-compiler"`. CUDA 12.8 supports up to VS 2022; VS 2026 triggers a version check error.

**Proxy interference**: Set `NO_PROXY=127.0.0.1,localhost` when running Python test scripts.

**Job timeout**: First request loads models into GPU memory — can take 1-3 minutes before generation starts.

**Out of VRAM**: Reduce `duration`, lower `vae-chunk`, or switch to CPU backend.

## Resources

### scripts/
- `build-gpu.cmd` — One-click CUDA build script for ace-server
- `test_generation.py` — Python script to generate songs via ace-server API (3 presets + custom mode)

### references/
- [build-guide.md](references/build-guide.md) — Build environment setup, MSVC+CUDA details, known issues
- [model-guide.md](references/model-guide.md) — Model selection, VRAM budget, inference parameter tuning
- [api-guide.md](references/api-guide.md) — Full ace-server HTTP API reference
- [lm-notes.md](references/lm-notes.md) — LM model behavior, pinyin output, prompt engineering tips
- [fullstack-deployment.md](references/fullstack-deployment.md) — Codi webapp full-stack setup, open-source modifications, database management, and troubleshooting
