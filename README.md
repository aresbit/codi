# Codi — 本地PC端 AI 音乐生成解决方案提供商

>trdl:Codi 让生产歌曲，像写代码一样简单。
>是一款仅需3060ti 8G显存 GPU 即可在本地电脑生成音乐的agent软件， 大模型提供商为ace-step。
> 适用硬件：NVIDIA RTX 3060 Ti (8GB VRAM)
> 模型：ACE-Step 1.5

---

## 为什么要本地部署

|   对比维度   | Suno（云端）             | Codi（本地 ACE-Step）         |
| :------: | -------------------- | ------------------------- |
| **商用授权** | ❌ 禁止商用，版权归属模糊        | ✅ **开源模型，商用自由**           |
| **数据隐私** | ❌ 歌词/创意上传至第三方服务器     | ✅ **数据不出本地，隐私绝对安全**       |
| **成本可控** | ❌ 订阅制 \$10-30/月，按量另计 | ✅ **一次性 GPU 投入，边际成本趋近于零** |
| **生成排队** | ❌ 高峰期排队，等待不可控        | ✅ **本地推理，秒级响应**           |
| **内容审查** | ❌ 平台审核，敏感词拦截         | ✅ **无审查，创作自由**            |
| **曲谱交付** | ❌ **不支持**            | ✅ **原生支持 MIDI → 五线谱渲染**   |
| **定制深度** | ❌ 黑盒，无法调参            | ✅ **开源可改，风格/结构完全可控**      |

一句话总结
Suno 是"租别人的琴房"，Codi 是"自己的录音棚"。
对于商业变现、隐私敏感 的场景，本地部署不是选择，是必需。

**Codi** 是目前唯一能在 8GB 显存上快速高效运行 ACE-Step 1.5 在PC端 提供**免费** AI 音乐生成解决方案的软件。

---

## 模型选择与显存预算

8GB 显存必须全部使用量化模型，且 DiT 要选偏 Turbo 的合并版本以提升速度。

| 组件 | 推荐文件 | 大小 | 来源 |
|------|---------|------|------|
| **DiT** | `acestep-v15-merge-sft-turbo-xl-ta-0.7-Q4_K_M.gguf` | ~2.85 GB | [scragnog/ace-step-1.5-gguf-merge-models](https://huggingface.co/scragnog/ace-step-1.5-gguf-merge-models) |
| **LM** | `acestep-5Hz-lm-4B-Q4_K_M.gguf` | ~2.1 GB | 官方 release |
| **Text Encoder** | `Qwen3-Embedding-0.6B-Q5_K_M.gguf` | ~0.45 GB | 官方 release |
| **VAE** | `vae-BF16.gguf` | ~0.32 GB | 官方 release |
| **总计** | | **~5.7 GB** | 留 2GB+ 给激活值和系统 |

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

## 致谢
- acestep.cpp https://github.com/ServeurpersoCom/acestep.cpp.git
- acestep https://github.com/ace-step/ACE-Step-1.5

## 开源许可
Apache-2.0
