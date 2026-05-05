# ace-server API Reference

Server listens on `http://127.0.0.1:8085` by default.

## Endpoints

### `GET /health`
Health check.
```json
{"status": "ok"}
```

### `GET /props`
Get server properties, model registry info, and all request parameters with defaults.

### `GET /logs`
Get recent server logs.

### `POST /lm` — Language Model Generation
Generate lyrics, BPM, key, and audio codes from text caption.

**Request:**
```json
{
  "lm_model": "acestep-5Hz-lm-4B-Q5_K_M.gguf",
  "synth_model": "acestep-v15-turbo-Q4_K_M.gguf",
  "caption": "Style description and lyrics theme...",
  "vocal_language": "zh",
  "duration": 180,
  "inference_steps": 8,
  "guidance_scale": 1.0,
  "shift": 3.0,
  "lm_mode": "generate",
  "output_format": "mp3"
}
```

**Response:**
```json
{"id": "job_id_hex"}
```

### `POST /synth` — Audio Synthesis
Synthesize audio from LM-generated enriched data.

**Request:** The JSON result from `/lm` (complete enriched object with lyrics, metadata, audio codes).
**Response:** `{"id": "job_id_hex"}`

### `GET /job` — Job Status Polling
| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | string | Job ID from `/lm` or `/synth` |
| `result` | string (opt) | Set to `"1"` to get result body |

**Status response** (no `result` param):
```json
{"status": "running|done|failed|cancelled"}
```

**Result response** (with `?result=1`):
- For `/lm`: Returns enriched JSON with `lyrics`, `bpm`, `keyscale`, `timesignature`, `duration`, and audio `codes`.
- For `/synth`: Returns binary MP3 (or WAV) audio.

## Generation Flow (Two-Phase)

```
Phase 1: LM
  POST /lm  ──→  job_id  ──→  poll GET /job?id=X  ──→ done
  GET /job?id=X&result=1  ──→  enriched JSON

Phase 2: Synth
  POST /synth  ──→  job_id  (send enriched JSON as body)
  poll GET /job?id=X  ──→  done
  GET /job?id=X&result=1  ──→  MP3 binary
```

## Important Headers

- **Content-Type**: `application/json` for POST bodies
- **Proxy issues**: If behind a local HTTP proxy, set `NO_PROXY=127.0.0.1,localhost` or use `httpx.Client()` with no proxy config.

## Timeouts

- Job polling interval: 2 seconds
- Max wait: 600 seconds (10 min) per job
- First request after startup is slower (model loading)
- LM phase: typically 1-3 minutes
- Synth phase: typically 20-60 seconds
