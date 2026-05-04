"""
视频合成器 — audio + 歌词字幕 + 曲谱图 → MP4
使用 MoviePy + FFmpeg
"""

import os
from pathlib import Path

OUTPUT_DIR = Path(os.getenv("SONGCRAFT_OUTPUT", "./output"))


def compose_video(audio_path: str, lyrics_text: str,
                  sheet_pngs: list[str] | None,
                  order_id: str, style_name: str) -> str:
    """
    合成最终交付 MP4：
    - 9:16 竖屏 (1080x1920)
    - 背景：纯色渐变 + 曲谱轮播
    - 歌词逐行滚动
    - 底部水印：AI定制歌曲
    """
    from moviepy import (
        AudioFileClip, ImageClip, TextClip,
        CompositeVideoClip, concatenate_videoclips,
    )
    from PIL import Image, ImageDraw, ImageFilter
    import numpy as np

    W, H = 1080, 1920
    order_dir = OUTPUT_DIR / order_id
    order_dir.mkdir(exist_ok=True)
    output_path = str(order_dir / f"{order_id}.mp4")

    audio = AudioFileClip(audio_path)
    duration = audio.duration

    # ---- 生成渐变背景 ----
    bg_path = str(order_dir / "bg.png")
    _make_gradient_background(W, H, bg_path)

    # ---- 曲谱展示（如果有） ----
    clips = []
    if sheet_pngs and len(sheet_pngs) > 0:
        sheet_clips = []
        sheet_dur = duration / len(sheet_pngs)
        for sp in sheet_pngs:
            sc = (ImageClip(sp)
                  .resized(height=H // 3)
                  .with_position(("center", H * 2 // 3 - 100))
                  .with_duration(sheet_dur))
            sheet_clips.append(sc)
        clips.extend(sheet_clips)

    # ---- 歌词字幕滚动 ----
    lyrics_lines = [l.strip() for l in lyrics_text.strip().split("\n") if l.strip()]
    if not lyrics_lines:
        lyrics_lines = [f"为你创作的一首{style_name}", "希望你喜欢 ❤"]

    lyric_clips = _make_lyrics_overlay(lyrics_lines, duration, W, H)
    clips.append(lyric_clips)

    # ---- 标题文本 ----
    title = (TextClip(f"AI 定制 · {style_name}", font_size=40, color="white",
                      font="PingFang-SC-Regular", stroke_color="black", stroke_width=1)
             .with_position(("center", 80))
             .with_duration(duration))
    clips.append(title)

    # ---- 底部水印 ----
    watermark = (TextClip("扫码定制你的专属歌曲", font_size=28, color="rgba(255,255,255,0.6)",
                          font="PingFang-SC-Regular")
                 .with_position(("center", H - 80))
                 .with_duration(duration))
    clips.append(watermark)

    # ---- 合成 ----
    bg_clip = ImageClip(bg_path).with_duration(duration)
    final = CompositeVideoClip([bg_clip] + clips, size=(W, H))
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
    """生成竖向渐变背景图，深蓝紫 → 深灰"""
    from PIL import Image, ImageDraw
    import numpy as np

    img = Image.new("RGB", (w, h))
    draw = ImageDraw.Draw(img)

    # 顶部颜色 → 底部颜色
    top_color = np.array([20, 30, 60])     # 深蓝
    bot_color = np.array([15, 15, 25])     # 深灰

    for y in range(h):
        t = y / h
        color = (top_color * (1 - t) + bot_color * t).astype(int)
        draw.line([(0, y), (w, y)], fill=tuple(color))

    img.save(output_path)


def _make_lyrics_overlay(lines: list[str], duration: float,
                         w: int, h: int):
    """
    歌词逐行显示在画面中央偏上。
    每行显示时间 = 总时长 / 行数
    """
    from moviepy import TextClip, concatenate_videoclips

    line_dur = duration / len(lines)

    lyric_clips = []
    for i, line in enumerate(lines):
        # 字体略大用于主歌词展示
        tc = (TextClip(line, font_size=52, color="white",
                       font="PingFang-SC-Regular",
                       stroke_color="black", stroke_width=2,
                       method="caption", size=(w - 120, None))
              .with_position(("center", h // 3))
              .with_start(i * line_dur)
              .with_duration(line_dur))
        lyric_clips.append(tc)

    return lyric_clips
