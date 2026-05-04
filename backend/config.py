"""
SongCraft — 泛音乐定制微信小程序后端
用户扫码 → 三步问卷 → 付钱 → ACE-Step生成歌曲 → MP4(歌词+曲谱)交付
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

PROMPT_TEMPLATE = """
[Music Generation Prompt]
Style: {style_name} — {style_tags}
Occasion: {occasion}
Audience: {audience}
Lyrics theme: Write lyrics in {language} about {theme}.
Personal touch: {personal_note}
Song structure: intro → verse1 → chorus → verse2 → chorus → bridge → chorus → outro.
Make the melody memorable and the arrangement professional.
IMPORTANT: Output the song with clear section markers [INTRO], [VERSE], [CHORUS], [BRIDGE], [OUTRO].
"""

PRICE_TIER_BASIC = 5.00    # MP4 + 歌词
PRICE_TIER_PREMIUM = 8.00  # MP4 + 歌词 + 曲谱
