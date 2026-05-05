# Codi acestep.cpp 本地部署指南

> 适用硬件：NVIDIA RTX 3060 Ti (8GB VRAM)
> 模型：ACE-Step 1.5

---

## 一、为什么必须本地部署

| 方案 | 3060Ti 可行性 | 说明 |
|------|--------------|------|
| 原生 PyTorch ACE-Step | ❌ 不可行 | FP16/BF16 下 DiT+LM 轻松超过 12GB |
| **acestep.cpp (GGML)** | ✅ **可行** | C++ 推理引擎，Q4_K_M 量化后全模型约 4-5GB |
| CPU 推理 | ⚠️ 太慢 | 歌曲生成耗时难以接受 |

**acestep.cpp** 是目前唯一能在 8GB 显存上运行 ACE-Step 1.5 的方案。

---

## 二、模型选择与显存预算

8GB 显存必须全部使用量化模型，且 DiT 要选偏 Turbo 的合并版本以提升速度。

| 组件 | 推荐文件 | 大小 | 来源 |
|------|---------|------|------|
| **DiT** | `acestep-v15-merge-sft-turbo-xl-ta-0.7-Q4_K_M.gguf` | ~2.85 GB | [scragnog/ace-step-1.5-gguf-merge-models](https://huggingface.co/scragnog/ace-step-1.5-gguf-merge-models) |
| **LM** | `acestep-5Hz-lm-4B-Q4_K_M.gguf` | ~2.1 GB | 官方 release |
| **Text Encoder** | `Qwen3-Embedding-0.6B-Q5_K_M.gguf` | ~0.45 GB | 官方 release |
| **VAE** | `vae-BF16.gguf` | ~0.32 GB | 官方 release |
| **总计** | | **~5.7 GB** | 留 2GB+ 给激活值和系统 |

> ⚠️ **关键限制**：LM 不能选 Q8_0，单文件约 8GB，加上其他组件必爆显存。

---

## 三、编译步骤

### 1. 克隆仓库

```bash
git clone --recurse-submodules https://github.com/ServeurpersoCom/acestep.cpp.git
cd acestep.cpp
```

### 2. 编译（CUDA 后端）

```bash
# Linux
./buildcuda.sh

# Windows
buildcuda.cmd
```

编译产物在 `build/` 目录下，主要可执行文件为 `ace-server`。

---

## 四、下载模型

在 `acestep.cpp/` 下创建 `models/` 目录，下载以下 4 个文件：

```bash
mkdir models
cd models

# DiT - 偏 Turbo 的合并模型（速度优先）
# 从 Hugging Face 下载:
# acestep-v15-merge-sft-turbo-xl-ta-0.7-Q4_K_M.gguf

# LM - 4B 量化版
# acestep-5Hz-lm-4B-Q4_K_M.gguf

# Text Encoder
# Qwen3-Embedding-0.6B-Q5_K_M.gguf

# VAE（固定 BF16，无法量化）
# vae-BF16.gguf
```

> 可使用 `huggingface-cli` 或浏览器手动下载。

---

## 五、启动服务

### 基础启动命令

```bash
./build/ace-server \
    --host 127.0.0.1 --port 8085 \
    --lm models/acestep-5Hz-lm-4B-Q4_K_M.gguf \
    --embedding models/Qwen3-Embedding-0.6B-Q5_K_M.gguf \
    --dit models/acestep-v15-merge-sft-turbo-xl-ta-0.7-Q4_K_M.gguf \
    --vae models/vae-BF16.gguf
```

### 8GB 显存优化参数（必加）

```bash
./build/ace-server \
    --host 127.0.0.1 --port 8085 \
    --lm models/acestep-5Hz-lm-4B-Q4_K_M.gguf \
    --embedding models/Qwen3-Embedding-0.6B-Q5_K_M.gguf \
    --dit models/acestep-v15-merge-sft-turbo-xl-ta-0.7-Q4_K_M.gguf \
    --vae models/vae-BF16.gguf \
    --vae-chunk 128 \
    --vae-overlap 32
```

| 参数 | 说明 |
|------|------|
| `--vae-chunk 128` | VAE 瓦片大小，降低显存峰值 |
| `--vae-overlap 32` | 瓦片重叠，减少接缝 |
| `--keep-loaded` | 常驻 VRAM（显存够时加，提升吞吐） |

### 显存仍不够时的降级方案

若 5.7GB 基础 + 激活值仍溢出：

1. DiT 降到 `merge-base-turbo-xl-ta-0.5-Q4_K_M`（更轻量）
2. 去掉 `--keep-loaded`，让模型按需加载
3. 终极方案：LM 放在 CPU 上（通过环境变量控制）

---

## 六、接入 Codi 后端

### 架构

```
webapp → FastAPI (port 8000) → acestep.cpp server (port 8085) → CUDA
```

### 修改 `backend/generator.py`

现有代码已支持 HTTP 调用模式，只需调整：

1. 设置环境变量：`ACE_STEP_API_URL=http://localhost:8085`
2. **适配 API 端点格式**：acestep.cpp 提供 `/lm`、`/synth`、`/understand`、`/vae` 四个底层端点，非一键生成
3. 需要手动编排调用流程：先 `/lm` 生成歌词/条件，再 `/synth` 生成音频

### 歌词生成适配

现有流程假设 ACE-Step 直接返回歌词文本。acestep.cpp 的 `/lm` 端点可以生成歌词，但输出格式需要验证是否与现有 `lyrics_text` 处理逻辑兼容。

---

## 七、故障排查

| 现象 | 原因 | 解决 |
|------|------|------|
| CUDA out of memory | 显存不足 | 加 `--vae-chunk`，或降级到更小模型 |
| 生成速度慢 | 步数太多 / 非 Turbo 模型 | 确认使用 ta-0.7 合并模型，减少推理步数 |
| 音频有接缝 | VAE 瓦片边界 | 增大 `--vae-overlap` |
| 模型加载失败 | GGUF 版本不兼容 | 确认下载的是 acestep.cpp 支持的 GGUF 格式 |

---

## 八、云端 API 备选

如果本地部署遇到问题，可考虑云端 API。但需注意：
- 需确认 API 服务商支持 ACE-Step 1.5
- 需确认定价和速率限制
- 当前测试的 `api.acemusic.ai` 服务端存在稳定性问题（详见测试报告）

---

## 九、下一步

1. 编译 acestep.cpp 并验证 CUDA 后端
2. 下载 4 个模型文件到 `models/`
3. 启动 ace-server
4. 修改 `generator.py` 适配 acestep.cpp HTTP API
5. 端到端测试生成流程
