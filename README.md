# Codi — AI 定制音乐

扫码 → 三步问卷 → 一首带歌词的 MP3/MP4 歌曲

## 项目结构

```
codi/
├── backend/                # Python 后端
│   ├── app.py              # FastAPI 主入口
│   ├── config.py           # 风格、场景、语言配置
│   ├── models.py           # SQLAlchemy 数据模型
│   ├── generator.py        # ACE-Step 音乐生成
│   ├── video.py            # MP4 合成 (音频 + 字幕)
│   └── requirements.txt
├── webapp/                 # React 前端
│   └── src/
└── README.md
```

## 快速开始

参考 [DEPLOY_GUIDE.md](DEPLOY_GUIDE.md) 部署 acestep.cpp 音乐引擎。

### 一键启动

```bash
# 确保 acestep 已编译且模型文件就绪后
双击 start.bat
```

## 用户流程

```
打开 Webapp → 三步问卷 → 生成歌曲 → 在线播放/下载
  ↓                   ↓                   ↓
选择受众/场合     选择风格/语言        MP3 + 可选 MP4
```

## 支持风格

山歌、民谣、流行情歌、摇滚、说唱、R&B、中国风、轻音乐
