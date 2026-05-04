"""
歌曲生成器 — 调用 ACE-Step 1.5 XL 生成音乐
通过 HTTP API 或本地 subprocess 调用
"""

import subprocess
import json
import os
import asyncio
from pathlib import Path
from config import PROMPT_TEMPLATE, STYLES, OCCASIONS, AUDIENCES

OUTPUT_DIR = Path(os.getenv("SONGCRAFT_OUTPUT", "./output"))
OUTPUT_DIR.mkdir(exist_ok=True)


def build_music_prompt(audience_key: str, occasion_key: str,
                       personal_note: str, style_key: str,
                       language: str = "zh") -> dict:
    """
    将用户三步输入 → ACE-Step 结构化 prompt
    返回 dict: {prompt_text, lyrics_prompt, style_tags, metadata}
    """

    style = STYLES.get(style_key, STYLES["pop_ballad"])
    occasion_text = OCCASIONS.get(occasion_key, occasion_key)
    audience_text = AUDIENCES.get(audience_key, audience_key)

    theme = occasion_text
    if personal_note:
        theme += f"，特别提到：{personal_note}"

    prompt_text = PROMPT_TEMPLATE.format(
        style_name=style["name"],
        style_tags=style["tags"],
        occasion=occasion_text,
        audience=audience_text,
        language="中文" if language == "zh" else "English",
        theme=theme,
        personal_note=personal_note or "无特殊要求",
    )

    return {
        "prompt": prompt_text.strip(),
        "style_name": style["name"],
        "style_tags": style["tags"],
        "language": language,
        "occasion": occasion_text,
        "audience": audience_text,
    }


async def generate_with_ace_step(prompt_data: dict, order_id: str) -> dict:
    """
    调用 ACE-Step 生成音乐。
    支持两种模式：
      1. 本地 HTTP API (推荐，ACE-Step 的 Gradio/FastAPI wrapper)
      2. 命令行 subprocess (直接调 Python 脚本)

    返回: {audio_path, lyrics_text, metadata}
    """

    prompt = prompt_data["prompt"]
    style_tags = prompt_data["style_tags"]
    language = prompt_data["language"]

    order_dir = OUTPUT_DIR / order_id
    order_dir.mkdir(exist_ok=True)

    # ---- 模式1: HTTP API (recommended) ----
    ace_api = os.getenv("ACE_STEP_API_URL", "http://localhost:7860")
    if ace_api:
        try:
            import httpx
            async with httpx.AsyncClient(timeout=300) as client:
                resp = await client.post(f"{ace_api}/generate", json={
                    "prompt": prompt,
                    "style": style_tags,
                    "lyrics_lang": language,
                    "duration": 180,  # 3 minutes max
                })
                if resp.status_code == 200:
                    result = resp.json()
                    audio_path = _save_audio(order_dir, result, order_id)
                    return {
                        "audio_path": str(audio_path),
                        "lyrics_text": result.get("lyrics", ""),
                        "sections": result.get("sections", {}),
                    }
        except Exception as e:
            # 如果 HTTP 失败，回退到命令行模式
            pass

    # ---- 模式2: CLI subprocess (fallback) ----
    lyrics_path = order_dir / f"{order_id}_lyrics.txt"
    audio_path = order_dir / f"{order_id}.wav"

    cmd = [
        "python", "-m", "ace_step.generate",
        "--prompt", prompt,
        "--style", style_tags,
        "--output", str(audio_path),
        "--lyrics-output", str(lyrics_path),
        "--duration", "180",
    ]

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()

    if proc.returncode != 0:
        raise RuntimeError(f"ACE-Step generation failed: {stderr.decode()}")

    lyrics_text = ""
    if lyrics_path.exists():
        lyrics_text = lyrics_path.read_text()

    return {
        "audio_path": str(audio_path),
        "lyrics_text": lyrics_text,
        "sections": {},
    }


def _save_audio(order_dir: Path, result: dict, order_id: str) -> Path:
    """保存ACE-Step返回的音频数据"""
    audio_path = order_dir / f"{order_id}.wav"
    if "audio_base64" in result:
        import base64
        audio_bytes = base64.b64decode(result["audio_base64"])
        audio_path.write_bytes(audio_bytes)
    elif "audio_url" in result:
        import httpx
        import asyncio
        async def download():
            async with httpx.AsyncClient() as c:
                r = await c.get(result["audio_url"])
                audio_path.write_bytes(r.content)
        asyncio.run(download())
    return audio_path
