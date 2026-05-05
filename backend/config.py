"""
Codi — AI 定制音乐后端
三步问卷 → ACE-Step生成歌曲 → MP3/MP4交付
"""

STYLES = {
    "mountain_song":     {"name": "山歌",     "tags": "folk mountain song, call and response, pentatonic, natural vocals, outdoor reverb"},
    "folk":              {"name": "民谣",     "tags": "acoustic folk, storytelling, guitar-driven, warm and intimate"},
    "pop_ballad":        {"name": "流行情歌", "tags": "pop ballad, emotional, piano, romantic, modern production"},
    "rock":              {"name": "摇滚",     "tags": "rock, electric guitar, drums, energetic, powerful"},
    "rap":               {"name": "说唱",     "tags": "hip-hop rap, rhythmic spoken word, beats, urban, confident flow"},
    "rnb":               {"name": "R&B",      "tags": "R&B, soulful, smooth vocals, groove, modern rhythm and blues"},
    "chinese_style":     {"name": "中国风",   "tags": "Chinese traditional style, guzheng, erhu, pentatonic melody, poetic"},
    "light_music":       {"name": "轻音乐",   "tags": "instrumental light music, ambient, relaxing, cinematic, no vocals"},
}

OCCASIONS = {
    "love":       "一首表达爱意的情歌",
    "proposal":   "一首浪漫的求婚歌曲",
    "wedding":    "一首祝福婚礼的歌曲",
    "birthday":   "一首温馨的生日祝福歌",
    "graduation": "一首关于毕业和未来的歌",
    "missing":    "一首表达思念的歌",
    "encourage":  "一首加油打气的励志歌曲",
    "thanks":     "一首表达感谢的歌",
    "new_year":   "一首年会/新年庆祝的歌",
}

AUDIENCES = {
    "lover":   "送给恋人或伴侣",
    "friend":  "送给朋友",
    "family":  "送给家人",
    "self":    "送给自己",
    "colleague": "送给同事或团队",
}

# 语言映射
LANGUAGE_MAP = {
    "zh":  {"label": "中文",      "vocal": "zh", "prompt_lang": "Chinese (Mandarin)"},
    "en":  {"label": "English",   "vocal": "en", "prompt_lang": "English"},
    "ja":  {"label": "日本語",    "vocal": "ja", "prompt_lang": "Japanese"},
    "ko":  {"label": "한국어",    "vocal": "ko", "prompt_lang": "Korean"},
    "fr":  {"label": "Français",  "vocal": "fr", "prompt_lang": "French"},
    "de":  {"label": "Deutsch",   "vocal": "de", "prompt_lang": "German"},
    "es":  {"label": "Español",   "vocal": "es", "prompt_lang": "Spanish"},
    "pt":  {"label": "Português", "vocal": "pt", "prompt_lang": "Portuguese"},
    "ru":  {"label": "Русский",   "vocal": "ru", "prompt_lang": "Russian"},
    "th":  {"label": "ไทย",       "vocal": "th", "prompt_lang": "Thai"},
    "vi":  {"label": "Tiếng Việt","vocal": "vi", "prompt_lang": "Vietnamese"},
}

PROMPT_TEMPLATE = """
[Music Generation Prompt]
Style: {style_name} — {style_tags}
Occasion: {occasion}
Audience: {audience}
Song structure: intro → verse1 → chorus → verse2 → chorus → bridge → chorus → outro.

IMPORTANT - LANGUAGE REQUIREMENT:
ALL lyrics must be written EXCLUSIVELY in {language}. Do NOT mix languages.
Every single word in the lyrics output must be in {language} only.
The vocals must be sung in {language}.
{chinese_hint}Lyrics theme: {theme}
Personal touch: {personal_note}

Output the song with clear section markers [INTRO], [VERSE], [CHORUS], [BRIDGE], [OUTRO].
Make the melody memorable and the arrangement professional.
"""

