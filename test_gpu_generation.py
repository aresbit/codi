"""
测试 acestep.cpp GPU 版本歌曲生成
直接调用 ace-server API，绕过后端支付流程
"""

import json
import os
import time
import httpx
import sys
from pathlib import Path

# 禁用代理（因为有本地 HTTP 代理在运行）
os.environ["NO_PROXY"] = "127.0.0.1,localhost"
os.environ["HTTP_PROXY"] = ""

ACE_URL = "http://127.0.0.1:8085"
OUTPUT_DIR = Path("./test_output4")
OUTPUT_DIR.mkdir(exist_ok=True)


def poll_job(client, job_id, timeout=600):
    """轮询 job 直到完成"""
    start = time.time()
    while True:
        if time.time() - start > timeout:
            raise TimeoutError(f"Job {job_id} 超时")
        resp = client.get(f"{ACE_URL}/job", params={"id": job_id})
        resp.raise_for_status()
        data = resp.json()
        status = data.get("status")
        print(f"  Job {job_id}: {status}")
        if status == "done":
            return
        if status in ("failed", "cancelled"):
            raise RuntimeError(f"Job {job_id} {status}")
        time.sleep(2)


def main():
    # ========== Phase 1: LM 生成歌词和参数 ==========
    caption = """Style: Evanescence-style Dark Symphonic Rock — piano-driven gothic rock with powerful female vocals, heavy guitar riffs, dramatic orchestral strings, dark and emotional atmosphere, soaring choruses with layered harmonies, ethereal piano verses, thunderous drums, classical elements blended with alternative metal. Cinematic, intense, melancholic yet uplifting.
Language: Japanese (romaji)
Vocal type: Powerful female soprano (Amy Lee style), ethereal and emotional with dramatic crescendos
Theme: Breaking free, soaring toward the endless blue sky, leaving the cage behind, pursuing light despite knowing you will fall. A journey of liberation, transformation, and chasing an unreachable dream.

Lyrics reference:
Habata itara modoranai to itte
Mezashita no wa aoi aoi ano sora

Kanashimi wa mada oboerarezu
Setsunasa wa ima tsukami hajimeta
Anata e to daku kono kanjou mo
Ima kotoba ni kawatte iku

Michinaru sekai no yume kara
Mezamete kono hane wo hiroge tobitatsu

Habata itara modoranai to itte
Mezashita no wa shiroi shiroi ano kumo
Tsukinuketara mitsukaru to shitte
Furikiru hodo aoi aoi ano sora

Kakedashitara te ni dekiru to itte
Izanau no wa tooi tooi ano koe
Mabushi sugita anata no te mo nigitte
Motomeru hodo aoi aoi ano sora

Ochite iku to wakatte ita
Soredemo hikari wo oi tsudzukete iku yo

Habata itara modoranai to itte
Sagashita no wa shiroi shiroi ano kumo
Tsukinuketara mitsukaru to shitte
Furikiru hodo aoi aoi ano sora

Song structure: piano intro → verse1 → pre-chorus → chorus → verse2 → chorus → bridge → final chorus → outro.
IMPORTANT: Output with clear section markers."""

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

    print("=" * 60)
    print("Phase 1: LM 生成歌词和参数")
    print("=" * 60)

    with httpx.Client(timeout=30.0) as client:
        # 提交 LM job
        resp = client.post(f"{ACE_URL}/lm", json=lm_request)
        resp.raise_for_status()
        lm_job = resp.json()
        lm_job_id = lm_job.get("id")
        print(f"LM job ID: {lm_job_id}")

        # 轮询 LM job
        poll_job(client, lm_job_id)

        # 获取 LM 结果
        resp = client.get(f"{ACE_URL}/job", params={"id": lm_job_id, "result": "1"})
        resp.raise_for_status()
        lm_result = resp.json()

    # 解析 LM 结果
    if isinstance(lm_result, list):
        lm_result = lm_result[0]

    lyrics = lm_result.get("lyrics", "")
    print(f"\n歌词 ({len(lyrics)} 字):")
    print("-" * 40)
    print(lyrics if lyrics else "(无歌词)")
    print("-" * 40)

    # 保存歌词
    lyrics_path = OUTPUT_DIR / "lyrics.txt"
    lyrics_path.write_text(lyrics, encoding="utf-8")
    print(f"歌词已保存: {lyrics_path}")

    # 打印 metadata
    print(f"\nBPM: {lm_result.get('bpm', 'N/A')}")
    print(f"Key/Scale: {lm_result.get('keyscale', 'N/A')}")
    print(f"Time Signature: {lm_result.get('timesignature', 'N/A')}")
    print(f"Duration: {lm_result.get('duration', 'N/A')}")

    # ========== Phase 2: Synth 合成音频 ==========
    print("\n" + "=" * 60)
    print("Phase 2: Synth 音频合成")
    print("=" * 60)

    with httpx.Client(timeout=30.0) as client:
        # 提交 synth job
        resp = client.post(f"{ACE_URL}/synth", json=lm_result)
        resp.raise_for_status()
        synth_job = resp.json()
        synth_job_id = synth_job.get("id")
        print(f"Synth job ID: {synth_job_id}")

        # 轮询 synth job
        poll_job(client, synth_job_id)

        # 下载结果（MP3 二进制）
        resp = client.get(f"{ACE_URL}/job", params={"id": synth_job_id, "result": "1"})
        resp.raise_for_status()

        audio_path = OUTPUT_DIR / "generated_song4.mp3"
        audio_path.write_bytes(resp.content)
        print(f"\n音频已保存: {audio_path}")
        print(f"文件大小: {len(resp.content) / 1024:.1f} KB")

    print("\n" + "=" * 60)
    print("生成完成！")
    print(f"  歌词: {lyrics_path}")
    print(f"  音频: {audio_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
