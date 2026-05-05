import type { Audience, Occasion, Style, StyleInfo, Language } from "@/types";

export const LANGUAGES: { key: Language; label: string }[] = [
  { key: "zh", label: "中文" },
  { key: "en", label: "English" },
  { key: "ja", label: "日本語" },
  { key: "ko", label: "한국어" },
  { key: "fr", label: "Français" },
  { key: "es", label: "Español" },
];

export const AUDIENCES: { key: Audience; label: string; icon: string; hint: string }[] = [
  { key: "lover",     label: "恋人", icon: "💕", hint: "送给你爱的人" },
  { key: "friend",    label: "朋友", icon: "🤝", hint: "送给兄弟或闺蜜" },
  { key: "family",    label: "家人", icon: "🏠", hint: "送给父母或亲人" },
  { key: "self",      label: "自己", icon: "🌟", hint: "为努力的自己" },
  { key: "colleague", label: "同事", icon: "💼", hint: "年会或项目庆祝" },
];

export const OCCASIONS: { key: Occasion; label: string }[] = [
  { key: "love",       label: "❤️ 表白 / 表达爱意" },
  { key: "proposal",   label: "💍 求婚" },
  { key: "wedding",    label: "💒 婚礼 / 纪念日" },
  { key: "birthday",   label: "🎂 生日" },
  { key: "graduation", label: "🎓 毕业" },
  { key: "missing",    label: "🌙 思念 / 异地" },
  { key: "encourage",  label: "💪 加油打气" },
  { key: "thanks",     label: "🙏 感谢" },
  { key: "new_year",   label: "🎉 年会 / 新年" },
];

export const STYLES: StyleInfo[] = [
  { key: "chinese_style", name: "中国风" },
  { key: "pop_ballad",    name: "流行情歌" },
  { key: "folk",          name: "民谣" },
  { key: "mountain_song", name: "山歌" },
  { key: "rock",          name: "摇滚" },
  { key: "rap",           name: "说唱" },
  { key: "rnb",           name: "R&B" },
  { key: "light_music",   name: "轻音乐" },
];
