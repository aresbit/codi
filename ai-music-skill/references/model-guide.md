# Model Selection & Inference Guide

## Recommended Models for RTX 3060 Ti (8GB VRAM)

| Role | Model File | Size | Quantization |
|------|-----------|------|-------------|
| LM (Lyrics + params) | `acestep-5Hz-lm-4B-Q5_K_M.gguf` | ~3.0 GB | Q5_K_M |
| DiT/Synth (Audio gen) | `acestep-v15-turbo-Q4_K_M.gguf` | ~1.4 GB | Q4_K_M |
| VAE (Audio decode) | `vae-BF16.gguf` | ~337 MB | BF16 |
| Text Encoder | `Qwen3-Embedding-0.6B-Q8_0.gguf` | ~784 MB | Q8_0 |

**Total VRAM**: ~5.5 GB → ~2.5 GB headroom for runtime.

## Model Download

Models auto-download via `models.sh` / `checkpoints.sh`, or manually from Hugging Face.

The server scans `--models <dir>` and auto-registers models by type (LM, DiT, VAE, Text-Enc).

## Inference Parameters (8GB Optimized)

| Parameter | Value | Why |
|-----------|-------|-----|
| `inference_steps` | 8 | Turbo variant: fewer steps = faster, still good quality. Base/SFT models use 50. |
| `guidance_scale` | 1.0 | Classifier-free guidance scale. 1.0 = no guidance (default for turbo). |
| `shift` | 3.0 | Flow matching shift. 3.0 = turbo default. Base/SFT = 1.0. |
| `duration` | 180 | Song length in seconds (3 min). Adjust as needed. |
| `vae-chunk` | 128 | Process VAE in chunks to reduce peak VRAM. |
| `vae-overlap` | 32 | Overlap between VAE chunks to avoid boundary artifacts. |

## Parameter Trade-offs

- **Higher inference_steps** (e.g., 24-50): Better audio quality, much slower, more VRAM.
- **Higher guidance_scale** (e.g., 3.0-7.0): More prompt adherence, but can distort audio.
- **Longer duration**: More VRAM for audio latent storage.
- **vae-chunk smaller**: Less VRAM, potentially slower (more chunks).

## Model Loading Order

On server startup, models load in this order:
1. Text Encoder (`Qwen3-Embedding`)
2. LM (`acestep-5Hz-lm`)
3. DiT/Synth (`acestep-v15-turbo`)
4. VAE (`vae-BF16`)

First request after startup will be slower (model loading). Subsequent requests reuse loaded models.

## Behavior Notes

- **LM model** outputs phoneme-level tokens (pinyin for Chinese, romaji for Japanese).
- **DiT model** synthesizes audio from text embeddings + audio latent codes.
- **VAE** decodes latent representation to waveform.
