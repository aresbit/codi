"""
歌曲生成器 — 调用 acestep.cpp 生成音乐
通过 HTTP API 连接本地 ace-server
"""

import json
import os
import asyncio
from pathlib import Path

# 务必在导入 httpx 之前清除代理变量，否则 httpx 会在导入时缓存代理配置
for _key in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"):
    os.environ.pop(_key, None)

import httpx
from httpx import AsyncHTTPTransport
from config import PROMPT_TEMPLATE, STYLES, OCCASIONS, AUDIENCES, LANGUAGE_MAP

OUTPUT_DIR = Path(os.getenv("CODI_OUTPUT", "./output"))
OUTPUT_DIR.mkdir(exist_ok=True)

# ---- acestep.cpp 配置 ----
ACE_SERVER_URL = os.getenv("ACE_SERVER_URL", "http://127.0.0.1:8085")
ACE_LM_MODEL = os.getenv("ACE_LM_MODEL", "acestep-5Hz-lm-4B-Q5_K_M.gguf")
ACE_SYNTH_MODEL = os.getenv("ACE_SYNTH_MODEL", "acestep-v15-turbo-Q4_K_M.gguf")

# 推理参数（8GB 显存优化）
ACE_INFERENCE_STEPS = int(os.getenv("ACE_INFERENCE_STEPS", "8"))
ACE_GUIDANCE_SCALE = float(os.getenv("ACE_GUIDANCE_SCALE", "1.0"))
ACE_SHIFT = float(os.getenv("ACE_SHIFT", "3.0"))
ACE_DURATION = int(os.getenv("ACE_DURATION", "360"))

# Job 轮询配置
JOB_POLL_INTERVAL = 2.0
JOB_MAX_WAIT = 600.0


def build_music_prompt(audience_key: str, occasion_key: str,
                       personal_note: str, style_key: str,
                       language: str = "zh",
                       exact_lyrics: str = "") -> dict:
    """
    将用户三步输入 -> acestep.cpp 结构化 prompt
    返回 dict: {prompt_text, lyrics_prompt, style_tags, metadata}
    exact_lyrics: 用户提供的完整歌词（可选），传入后将使用 format 模式，不修改歌词
    """

    style = STYLES.get(style_key, STYLES["pop_ballad"])
    occasion_text = OCCASIONS.get(occasion_key, occasion_key)
    audience_text = AUDIENCES.get(audience_key, audience_key)

    lang_info = LANGUAGE_MAP.get(language, LANGUAGE_MAP["en"])
    prompt_lang = lang_info["prompt_lang"]
    vocal_lang = lang_info["vocal"]

    theme = occasion_text
    if personal_note:
        theme += f"，特别提到：{personal_note}"

    chinese_hint = ""
    if language == "zh":
        chinese_hint = 'CRITICAL: 歌词必须使用汉字书写，绝对不要使用拼音！例如写"你好"而不是"ni hao"。\n'

    prompt_text = PROMPT_TEMPLATE.format(
        style_name=style["name"],
        style_tags=style["tags"],
        occasion=occasion_text,
        audience=audience_text,
        language=prompt_lang,
        chinese_hint=chinese_hint,
        theme=theme,
        personal_note=personal_note or "无特殊要求",
    )

    return {
        "prompt": prompt_text.strip(),
        "style_name": style["name"],
        "style_tags": style["tags"],
        "language": language,
        "vocal_lang": vocal_lang,
        "occasion": occasion_text,
        "audience": audience_text,
        "exact_lyrics": exact_lyrics.strip(),
    }


async def generate_with_ace_step(prompt_data: dict, order_id: str) -> dict:
    """
    调用 acestep.cpp 生成音乐。

    流程：
      1. POST /lm   -> 生成歌词和参数（异步 job）
      2. GET  /job  -> 轮询直到完成，获取 enriched JSON
      3. POST /synth -> 合成音频（异步 job）
      4. GET  /job  -> 轮询直到完成，获取 MP3

    返回: {audio_path, lyrics_text, metadata}
    """

    order_dir = OUTPUT_DIR / order_id
    order_dir.mkdir(exist_ok=True)

    caption = prompt_data["prompt"]
    vocal_lang = prompt_data["vocal_lang"]
    exact_lyrics = prompt_data.get("exact_lyrics", "")

    # 判断是否使用用户提供的精确歌词
    use_format_mode = bool(exact_lyrics)

    # ---- Phase 1: LM 生成歌词和参数 ----
    lm_request = {
        "lm_model": ACE_LM_MODEL,
        "synth_model": ACE_SYNTH_MODEL,
        "caption": caption,
        "vocal_language": vocal_lang,
        "duration": ACE_DURATION,
        "inference_steps": ACE_INFERENCE_STEPS,
        "guidance_scale": ACE_GUIDANCE_SCALE,
        "shift": ACE_SHIFT,
    }

    if use_format_mode:
        # format 模式: 使用用户提供的歌词，不修改
        lm_request["lm_mode"] = "format"
        lm_request["lyrics"] = exact_lyrics
        print(f"[INFO] Using format mode with user-provided lyrics ({len(exact_lyrics)} chars)", flush=True)
    else:
        # generate 模式: AI 自主生成歌词
        lm_request["lm_mode"] = "generate"
        print("[INFO] Using generate mode (AI will create lyrics)", flush=True)

    async with httpx.AsyncClient(timeout=30.0, transport=AsyncHTTPTransport(proxy=None)) as client:
        # 1) 提交 LM job
        print(f"[DEBUG] HTTP_PROXY={os.environ.get('HTTP_PROXY', 'NOT SET')}", flush=True)
        print(f"[DEBUG] POST to {ACE_SERVER_URL}/lm", flush=True)
        resp = await client.post(
            f"{ACE_SERVER_URL}/lm",
            json=lm_request,
        )
        resp.raise_for_status()
        lm_job = resp.json()
        lm_job_id = lm_job.get("id")
        if not lm_job_id:
            raise RuntimeError(f"LM job 提交失败，响应: {lm_job}")

        # 2) 轮询 LM job
        lm_result = await _poll_job(client, lm_job_id)

    # 解析 LM 结果
    enriched = lm_result
    if isinstance(enriched, list):
        enriched = enriched[0]

    # format 模式: 直接使用用户提供的原始歌词
    # generate 模式: 使用 LM 生成的歌词
    if use_format_mode:
        lyrics_text = exact_lyrics
    else:
        lyrics_text = enriched.get("lyrics", "")
        if not lyrics_text:
            lyrics_text = caption

    # ---- Phase 2: Synth 合成音频 ----
    async with httpx.AsyncClient(timeout=30.0, transport=AsyncHTTPTransport(proxy=None)) as client:
        # 3) 提交 synth job
        resp = await client.post(
            f"{ACE_SERVER_URL}/synth",
            json=enriched,
        )
        resp.raise_for_status()
        synth_job = resp.json()
        synth_job_id = synth_job.get("id")
        if not synth_job_id:
            raise RuntimeError(f"Synth job 提交失败，响应: {synth_job}")

        # 4) 轮询 synth job 并获取结果（MP3 二进制）
        audio_path = await _poll_job_and_download(
            client, synth_job_id, order_dir, order_id
        )

    return {
        "audio_path": str(audio_path),
        "lyrics_text": lyrics_text,
        "sections": enriched.get("sections", {}),
        "metadata": {
            "bpm": enriched.get("bpm"),
            "keyscale": enriched.get("keyscale"),
            "timesignature": enriched.get("timesignature"),
            "duration": enriched.get("duration"),
        },
    }


async def _poll_job(client: httpx.AsyncClient, job_id: str) -> dict:
    """轮询 job 直到完成，返回 JSON 结果。"""
    waited = 0.0
    while waited < JOB_MAX_WAIT:
        resp = await client.get(
            f"{ACE_SERVER_URL}/job",
            params={"id": job_id},
        )
        resp.raise_for_status()
        status_data = resp.json()
        status = status_data.get("status")

        if status == "done":
            # 获取结果
            resp = await client.get(
                f"{ACE_SERVER_URL}/job",
                params={"id": job_id, "result": "1"},
            )
            resp.raise_for_status()
            return resp.json()

        if status in ("failed", "cancelled"):
            raise RuntimeError(f"Job {job_id} {status}")

        await asyncio.sleep(JOB_POLL_INTERVAL)
        waited += JOB_POLL_INTERVAL

    raise RuntimeError(f"Job {job_id} 超时（>{JOB_MAX_WAIT}s）")


async def _poll_job_and_download(
    client: httpx.AsyncClient,
    job_id: str,
    order_dir: Path,
    order_id: str,
) -> Path:
    """轮询 job 直到完成，下载二进制结果（MP3）到文件。"""
    waited = 0.0
    while waited < JOB_MAX_WAIT:
        resp = await client.get(
            f"{ACE_SERVER_URL}/job",
            params={"id": job_id},
        )
        resp.raise_for_status()
        status_data = resp.json()
        status = status_data.get("status")

        if status == "done":
            # 下载结果（二进制 MP3）
            resp = await client.get(
                f"{ACE_SERVER_URL}/job",
                params={"id": job_id, "result": "1"},
            )
            resp.raise_for_status()

            audio_path = order_dir / f"{order_id}.mp3"
            audio_path.write_bytes(resp.content)
            return audio_path

        if status in ("failed", "cancelled"):
            raise RuntimeError(f"Job {job_id} {status}")

        await asyncio.sleep(JOB_POLL_INTERVAL)
        waited += JOB_POLL_INTERVAL

    raise RuntimeError(f"Job {job_id} 下载超时（>{JOB_MAX_WAIT}s）")


def _save_audio(order_dir: Path, result: dict, order_id: str) -> Path:
    """保存ACE-Step返回的音频数据（兼容旧逻辑）"""
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
