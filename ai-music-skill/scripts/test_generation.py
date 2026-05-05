"""
Test acestep.cpp song generation via ace-server API.
Usage: python test_generation.py [--output-dir ./output] [--url http://127.0.0.1:8085]
"""

import json
import os
import sys
import time
import argparse
from pathlib import Path

import httpx

# Bypass local HTTP proxies
os.environ["NO_PROXY"] = "127.0.0.1,localhost"
os.environ["HTTP_PROXY"] = ""
os.environ["HTTPS_PROXY"] = ""


def poll_job(client: httpx.Client, job_id: str, timeout: int = 600) -> None:
    """Poll job until done or timeout."""
    start = time.time()
    while True:
        if time.time() - start > timeout:
            raise TimeoutError(f"Job {job_id} timed out after {timeout}s")
        resp = client.get(f"{ACE_URL}/job", params={"id": job_id})
        resp.raise_for_status()
        status = resp.json().get("status")
        print(f"  Job {job_id}: {status}")
        if status == "done":
            return
        if status in ("failed", "cancelled"):
            raise RuntimeError(f"Job {job_id} {status}")
        time.sleep(2)


def generate_song(caption: str, output_dir: Path) -> dict:
    """Run two-phase generation: LM → Synth."""

    lm_request = {
        "lm_model": "acestep-5Hz-lm-4B-Q5_K_M.gguf",
        "synth_model": "acestep-v15-turbo-Q4_K_M.gguf",
        "caption": caption,
        "vocal_language": "zh",
        "duration": 180,
        "inference_steps": 8,
        "guidance_scale": 1.0,
        "shift": 3.0,
        "lm_mode": "generate",
        "output_format": "mp3",
    }

    # Phase 1: LM
    print("=" * 60)
    print("Phase 1: LM — lyrics + parameters")
    print("=" * 60)

    with httpx.Client(timeout=30.0) as client:
        resp = client.post(f"{ACE_URL}/lm", json=lm_request)
        resp.raise_for_status()
        lm_job_id = resp.json().get("id")
        print(f"LM job ID: {lm_job_id}")
        poll_job(client, lm_job_id)

        resp = client.get(f"{ACE_URL}/job", params={"id": lm_job_id, "result": "1"})
        resp.raise_for_status()
        lm_result = resp.json()

    if isinstance(lm_result, list):
        lm_result = lm_result[0]

    lyrics = lm_result.get("lyrics", "")
    lyrics_path = output_dir / "lyrics.txt"
    lyrics_path.write_text(lyrics, encoding="utf-8")

    print(f"\nLyrics ({len(lyrics)} chars):")
    print("-" * 40)
    print(lyrics if lyrics else "(empty)")
    print("-" * 40)
    print(f"BPM: {lm_result.get('bpm', 'N/A')}")
    print(f"Key: {lm_result.get('keyscale', 'N/A')}")
    print(f"Time: {lm_result.get('timesignature', 'N/A')}")
    print(f"Duration: {lm_result.get('duration', 'N/A')}s")
    print(f"Lyrics saved: {lyrics_path}")

    # Phase 2: Synth
    print("\n" + "=" * 60)
    print("Phase 2: Synth — audio generation")
    print("=" * 60)

    with httpx.Client(timeout=30.0) as client:
        resp = client.post(f"{ACE_URL}/synth", json=lm_result)
        resp.raise_for_status()
        synth_job_id = resp.json().get("id")
        print(f"Synth job ID: {synth_job_id}")
        poll_job(client, synth_job_id)

        resp = client.get(f"{ACE_URL}/job", params={"id": synth_job_id, "result": "1"})
        resp.raise_for_status()

        audio_path = output_dir / "song.mp3"
        audio_path.write_bytes(resp.content)
        print(f"\nAudio saved: {audio_path} ({len(resp.content) / 1024:.1f} KB)")

    return {
        "lyrics_path": str(lyrics_path),
        "audio_path": str(audio_path),
        "bpm": lm_result.get("bpm"),
        "keyscale": lm_result.get("keyscale"),
    }


# ============================================================
# Example captions for quick reference
# ============================================================

CAPTION_FOLK = """Style: Acoustic Folk, Indie Pop — acoustic folk, storytelling, guitar-driven, warm female vocals, gentle piano, emotional, nostalgic, calm, mid-tempo.
Theme: A heartfelt thank-you to the hardworking people who make the world beautiful.
Language: Chinese
Structure: intro → verse → chorus → verse → chorus → bridge → chorus → outro."""

CAPTION_EVANESCENCE = """Style: Evanescence Dark Symphonic Rock — piano-driven gothic rock, powerful female vocals, heavy guitar riffs, dramatic orchestral strings, dark emotional atmosphere, soaring layered choruses, ethereal piano verses, thunderous drums.
Theme: Breaking free, soaring toward the endless sky, leaving the cage behind.
Language: Chinese
Structure: intro → verse → pre-chorus → chorus → breakdown → bridge → final chorus → outro."""

CAPTION_POWER_BALLAD = """Style: Cinematic Power Ballad — piano and lush strings, warm male vocals, electric guitar solo, driving drums, intimate verses building to soaring anthemic choruses, wide dynamic range, orchestral rock production.
Theme: Falling into the river of love, journeying to the ends of the earth with a beloved.
Language: Chinese
Structure: intro → verse1 → chorus → verse2 → chorus → guitar solo → bridge → final chorus → outro."""


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate music via ace-server API")
    parser.add_argument("--url", default="http://127.0.0.1:8085", help="ace-server URL")
    parser.add_argument("--output", default="./song_output", help="Output directory")
    parser.add_argument("--caption", default="folk", choices=["folk", "evanescence", "ballad", "custom"],
                        help="Preset caption style or 'custom'")
    parser.add_argument("--custom-text", help="Custom caption text (required if --caption=custom)")
    args = parser.parse_args()

    global ACE_URL
    ACE_URL = args.url

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    captions = {
        "folk": CAPTION_FOLK,
        "evanescence": CAPTION_EVANESCENCE,
        "ballad": CAPTION_POWER_BALLAD,
    }

    if args.caption == "custom":
        if not args.custom_text:
            print("ERROR: --custom-text required when --caption=custom")
            sys.exit(1)
        caption = args.custom_text
    else:
        caption = captions[args.caption]

    try:
        result = generate_song(caption, output_dir)
        print("\n" + "=" * 60)
        print("Generation complete!")
        print(f"  Lyrics: {result['lyrics_path']}")
        print(f"  Audio:  {result['audio_path']}")
        print(f"  BPM:    {result['bpm']}")
        print(f"  Key:    {result['keyscale']}")
        print("=" * 60)
    except Exception as e:
        print(f"\nERROR: {e}")
        sys.exit(1)
