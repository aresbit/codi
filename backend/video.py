"""
视频合成器 — audio + 歌词字幕 → MP4
"""

import os
from pathlib import Path

OUTPUT_DIR = Path(os.getenv("CODI_OUTPUT", "./output"))


def compose_video(audio_path: str, lyrics_text: str,
                  order_id: str, style_name: str) -> str:
    """
    合成 MP4：
    - 9:16 竖屏 (1080x1920)
    - 背景纯色渐变
    - 歌词逐行滚动
    - 底部水印
    """
    from moviepy import (
        AudioFileClip, ImageClip, TextClip,
        CompositeVideoClip,
    )
    import numpy as np

    W, H = 1080, 1920
    order_dir = OUTPUT_DIR / order_id
    order_dir.mkdir(exist_ok=True)
    output_path = str(order_dir / f"{order_id}.mp4")

    # 预转换 MP3 → WAV
    wav_path = audio_path.rsplit(".", 1)[0] + ".wav"
    if audio_path.endswith(".mp3") and not os.path.isfile(wav_path):
        import subprocess as _sp
        _sp.run(
            ["ffmpeg", "-y", "-i", audio_path, "-acodec", "pcm_s16le",
             "-ar", "44100", "-ac", "2", wav_path],
            capture_output=True, timeout=120,
        )
        audio_path = wav_path

    audio = AudioFileClip(audio_path)
    duration = audio.duration

    # 渐变背景
    bg_path = str(order_dir / "bg.png")
    _make_gradient_background(W, H, bg_path)

    # 歌词字幕滚动
    lyrics_lines = [l.strip() for l in lyrics_text.strip().split("\n") if l.strip()]
    if not lyrics_lines:
        lyrics_lines = [f"为你创作的一首{style_name}", "希望你喜欢"]

    lyric_clips = _make_lyrics_overlay(lyrics_lines, duration, W, H)

    # 标题
    title = (TextClip(text=f"AI 定制 · {style_name}", font="msyh.ttc",
                      font_size=40, color="white",
                      stroke_color="black", stroke_width=1)
             .with_position(("center", 80))
             .with_duration(duration))

    # 底部水印
    watermark = (TextClip(text="Codi · AI 定制歌曲", font="msyh.ttc",
                          font_size=28, color="white")
                 .with_position(("center", H - 80))
                 .with_duration(duration))

    # 合成
    bg_clip = ImageClip(bg_path).with_duration(duration)
    final = CompositeVideoClip([bg_clip, title, watermark] + lyric_clips, size=(W, H))
    final = final.with_audio(audio)

    final.write_videofile(
        output_path,
        fps=24,
        codec="libx264",
        audio_codec="aac",
        preset="medium",
        threads=4,
    )

    return output_path


def _make_gradient_background(w: int, h: int, output_path: str):
    """竖向渐变背景 (深蓝紫 → 深灰)"""
    from PIL import Image, ImageDraw
    import numpy as np

    img = Image.new("RGB", (w, h))
    draw = ImageDraw.Draw(img)

    top_color = np.array([20, 30, 60])
    bot_color = np.array([15, 15, 25])

    for y in range(h):
        t = y / h
        color = (top_color * (1 - t) + bot_color * t).astype(int)
        draw.line([(0, y), (w, y)], fill=tuple(color))

    img.save(output_path)


def _make_lyrics_overlay(lines: list[str], duration: float,
                         w: int, h: int):
    """歌词逐行显示在画面中央偏上"""
    from moviepy import TextClip

    line_dur = duration / len(lines)

    lyric_clips = []
    for i, line in enumerate(lines):
        tc = (TextClip(text=line, font="msyh.ttc",
                       font_size=52, color="white",
                       stroke_color="black", stroke_width=2,
                       method="caption", size=(w - 120, None))
              .with_position(("center", h // 3))
              .with_start(i * line_dur)
              .with_duration(line_dur))
        lyric_clips.append(tc)

    return lyric_clips
