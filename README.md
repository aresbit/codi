# SongCraft — AI 定制音乐微信小程序

扫码 → 三步问卷 → 付钱 → 一首带歌词+曲谱的 MP4 歌曲

## 卖点

- 市面上所有 AI 音乐小程序都没有曲谱交付，SongCraft 有
- 不绑 Suno，用开源 ACE-Step 1.5 XL（质量超 Suno v5，商用许可）
- 引导式三步问卷，用户不需要懂 AI
- 梯度定价：¥5 基础版 / ¥8 完整版（+曲谱）

## 项目结构

```
songcraft/
├── backend/                # Python 后端
│   ├── app.py              # FastAPI 主入口
│   ├── config.py           # 风格、场景、定价配置
│   ├── models.py           # SQLAlchemy 数据模型
│   ├── generator.py        # ACE-Step 音乐生成
│   ├── notation.py         # 曲谱渲染 (midi → sheet music PNG)
│   ├── video.py            # MP4 合成 (音频 + 字幕 + 曲谱)
│   ├── payment.py          # 微信支付集成
│   └── requirements.txt
├── miniprogram/            # 微信小程序前端
│   ├── app.js / app.json / app.wxss
│   ├── pages/
│   │   ├── index/          # 首页 (风格预览 + 套餐选择)
│   │   ├── create/         # 三步问卷 (受众 → 场合 → 风格)
│   │   ├── pay/            # 支付确认页
│   │   └── result/         # 结果页 (播放 + 下载 + 分享)
│   └── utils/api.js        # 后端 API 封装
└── README.md
```

## 快速开始

### 1. 后端

```bash
cd backend

# 安装依赖
pip install -r requirements.txt --break-system-packages

# 安装 LilyPond (曲谱渲染)
# macOS: brew install lilypond
# Ubuntu: apt install lilypond
# 或跳过曲谱，只用基础版

# 设置环境变量
export ACE_STEP_API_URL="http://localhost:7860"  # ACE-Step Gradio API
export WX_APPID="your_wechat_appid"              # 微信小程序 AppID
export WX_MCHID="your_merchant_id"               # 微信商户号
export WX_API_KEY="your_api_key"                 # 微信 APIv3 密钥
export WX_MCH_SERIAL="your_cert_serial"          # 商户证书序列号
export WX_PRIVATE_KEY_PATH="/path/to/apiclient_key.pem"
export WX_NOTIFY_URL="https://your-domain.com/api/pay/notify"

# 启动
python app.py
# 服务运行在 http://localhost:8000
```

### 2. ACE-Step 1.5 XL 部署

```bash
git clone https://github.com/ace-step/ACE-Step
cd ACE-Step
pip install -r requirements.txt --break-system-packages

# 下载模型 (约 8GB)
python download_model.py

# 启动 Gradio API
python app.py --api --port 7860
# 最低 4GB 显存即可运行
```

### 3. 微信小程序

1. 注册微信小程序：https://mp.weixin.qq.com
2. 在 `app.js` 中修改 `baseUrl` 为你的后端域名
3. 在微信开发者工具中打开 `miniprogram/` 目录
4. 配置服务器域名白名单 (request 合法域名)
5. 如需支付：开通微信商户号，配置 JSAPI 支付

### 4. 测试（免微信支付）

MVP 测试模式下，后端在微信支付不可用时会自动降级为测试模式：
- 创建订单后直接标记为"可生成"
- 不需要真实支付
- 适合本地开发验证完整流程

## 用户流程

```
扫码进入小程序
  ↓
首页：选择套餐 (¥5基础 / ¥8完整)
  ↓
三步问卷：
  第1步 → 这首歌给谁的？(恋人/朋友/家人/自己/同事)
  第2步 → 什么场合？(表白/婚礼/生日/毕业/思念/加油/感谢/年会)
  第3步 → 选风格 (8种) + 特别的话 (选填)
  ↓
确认支付 → 微信支付
  ↓
后台生成 (1-3分钟)：
  ACE-Step 生成音频
  → music21+LilyPond 渲染曲谱 (premium)
  → MoviePy+FFmpeg 合成 MP4 (歌词字幕 + 曲谱图 + 背景)
  ↓
结果页：在线播放、下载MP4、下载曲谱、分享
```

## 时间成本

每首歌约 1-3 分钟生成：
- ACE-Step 推理：15-30 秒 (RTX 3090)
- 曲谱渲染：10-20 秒
- 视频合成：30-60 秒

## 经济模型

| 项目 | 金额 |
|------|------|
| 基础版售价 | ¥5.00 |
| 完整版售价 | ¥8.00 |
| ACE-Step 推理成本 | ≈¥0 (自有 GPU 电费) |
| 曲谱渲染成本 | ≈¥0.05 (CPU) |
| 视频合成成本 | ≈¥0.10 (CPU) |
| 微信支付手续费 | 0.6% |
| **基础版毛利** | ≈¥4.85 |
| **完整版毛利** | ≈¥7.85 |

每卖 100 首完整版 ≈ ¥785 收入，扣掉服务器和带宽，token 钱够用了。

## 支持风格

山歌、民谣、流行情歌、摇滚、说唱、R&B、中国风、轻音乐
