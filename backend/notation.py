"""
曲谱生成器 — music21 + LilyPond 渲染五线谱/简谱为 PNG
"""

import os
from pathlib import Path

OUTPUT_DIR = Path(os.getenv("SONGCRAFT_OUTPUT", "./output"))


def audio_to_midi(audio_path: str) -> str:
    """
    音频 → MIDI 转录。
    使用 basic-pitch (Spotify) 或 librosa 做音高检测。
    """
    midi_path = audio_path.replace(".wav", ".mid").replace(".mp3", ".mid")
    if Path(midi_path).exists():
        return midi_path

    try:
        from basic_pitch.inference import predict
        from basic_pitch import ICASSP_2022_MODEL_PATH
        import tensorflow as tf

        model = tf.saved_model.load(str(ICASSP_2022_MODEL_PATH))
        _, midi_data, _ = predict(audio_path, model)
        midi_data.write(midi_path)
    except ImportError:
        # fallback: 用 librosa 提取主旋律音高，手工造MIDI
        _simple_pitch_to_midi(audio_path, midi_path)

    return midi_path


def _simple_pitch_to_midi(audio_path: str, midi_path: str):
    """简易音高 → MIDI fallback"""
    import librosa
    import numpy as np
    from music21 import stream, note, tempo, meter, metadata

    y, sr = librosa.load(audio_path, sr=22050)
    f0, _, _ = librosa.pyin(y, fmin=80, fmax=1200, sr=sr)

    valid = ~np.isnan(f0)
    f0_valid = f0[valid]
    times = librosa.frames_to_time(np.arange(len(f0))[valid], sr=sr)

    midi_notes = librosa.hz_to_midi(f0_valid)

    s = stream.Score()
    p = stream.Part()
    p.append(tempo.MetronomeMark(number=120))
    p.append(meter.TimeSignature("4/4"))
    p.append(metadata.Metadata(title="AI Generated Song"))

    # 按时间分组为音符
    quarter_duration = 0.5  # 120bpm 下四分音符 = 0.5秒
    for i, (t, mn) in enumerate(zip(times, midi_notes)):
        dur = quarter_duration
        if i + 1 < len(times):
            dur = min(times[i + 1] - t, quarter_duration * 4)
        n = note.Note(int(round(mn)))
        n.duration.quarterLength = dur / quarter_duration
        n.offset = t
        p.append(n)

    s.append(p)
    s.write("midi", midi_path)


def midi_to_sheet_music_png(midi_path: str, output_dir: str) -> list[str]:
    """
    MIDI → 五线谱 PNG (via music21 + LilyPond)
    返回 PNG 文件路径列表（多页曲谱）
    """
    from music21 import converter

    score = converter.parse(midi_path)

    # 拆分成多个小节便于阅读
    measures_per_line = 4
    png_paths = []

    key_signature = score.analyze("key")
    for part in score.parts:
        part.keySignature = key_signature

    # 导出 LilyPond 再转 PNG
    lily_path = os.path.join(output_dir, "sheet.ly")
    score.write("lilypond", lily_path)

    try:
        import subprocess
        subprocess.run(
            ["lilypond", "--png", "-o", os.path.join(output_dir, "sheet"), lily_path],
            capture_output=True, timeout=60,
        )
        # 收集生成的 PNG
        for f in sorted(Path(output_dir).glob("sheet*.png")):
            png_paths.append(str(f))
    except Exception:
        # LilyPond 不可用时，用 music21 内置 MuseScore 渲染
        png_path = os.path.join(output_dir, "sheet_music.png")
        score.write("musicxml.png", png_path)
        png_paths.append(png_path)

    return png_paths


def generate_sheet_music(audio_path: str, order_id: str) -> list[str]:
    """一站式：音频 → MIDI → 曲谱PNG"""
    order_dir = OUTPUT_DIR / order_id
    order_dir.mkdir(exist_ok=True)

    midi_path = audio_to_midi(audio_path)
    return midi_to_sheet_music_png(midi_path, str(order_dir))
