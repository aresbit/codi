# Full-Stack Deployment — Codi Webapp

基于 acestep.cpp 的完整 Web 应用部署指南。

## 架构概览

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│  Webapp      │ ──→ │  FastAPI     │ ──→ │  ace-server  │
│  Vite+React  │     │  Backend     │     │  acestep.cpp │
│  :5173/5174  │     │  :8000       │     │  :8085       │
└─────────────┘     └──────────────┘     └──────────────┘
                          │
                    ┌─────┴─────┐
                    │  SQLite   │
                    │  codi    │
                    │   .db     │
                    └───────────┘
```

### 三层服务
| 服务 | 端口 | 技术栈 | 用途 |
|------|------|--------|------|
| ace-server | 8085 | acestep.cpp + CUDA | AI 音乐生成引擎 |
| Backend | 8000 | FastAPI + SQLAlchemy | API 服务 + 业务流程 |
| Webapp | 5173/4 | Vite + React + Tailwind | 用户界面 |

## 启动顺序

**必须先启动 acestep，再启动 backend，最后 webapp。**

```bash
# 1. acestep (GPU)
cd /path/to/acestep
./start-server-gpu.sh
# 验证: curl http://127.0.0.1:8085/health

# 2. Backend
cd /path/to/codi/backend
python -m uvicorn app:app --host 0.0.0.0 --port 8000
# 注意: Windows 上必须用 python -m uvicorn，直接 uvicorn 可能找不到命令
# 验证: curl http://127.0.0.1:8000/api/health

# 3. Webapp
cd /path/to/codi/webapp
npx vite --host
# 验证: 浏览器打开 http://localhost:5173
```

## Webapp 配置

### API 代理 (vite.config.ts)
```ts
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',  // 必须匹配 backend 端口
      changeOrigin: true,
    },
  },
}
```
- 端口 5173 被占用时 Vite 会自动切换到 5174
- proxy target 必须与 backend 实际端口一致

## 数据管理

### SQLite 数据库
- 位置: `backend/codi.db`
- 表结构变更后需要删除重建:
  ```bash
  rm backend/codi.db  # 删除后重启 backend 自动创建
  ```
- ORM: SQLAlchemy + aiosqlite (异步)

### Order 模型字段
```
id, status, audience, occasion, personal_note, style, language,
generate_video, lyrics, audio_url, video_url, error_message,
created_at, completed_at
```

## 生成流程

```
用户提交 → POST /api/orders
  → 创建 Order(status=generating)
  → background_tasks.add_task(_generate_song)
    ↓
  Phase 1: build_music_prompt() → 组装 prompt
  Phase 2: POST /lm → 轮询 job → enriched JSON (歌词+参数)
  Phase 3: POST /synth → 轮询 job → MP3 二进制
  Phase 4 (可选): compose_video() → MP4 合成
  Phase 5: 更新 Order(status=completed, audio_url, video_url)
    ↓
前端轮询 GET /api/orders/{id} → 展示结果
```

## 关键改动（开源化）

### 已移除
- 曲谱生成 (notation.py) — 删除
- 微信支付 (payment.py) — 删除
- 套餐/tier/price — 完全免费
- 支付状态 — 创建即开始生成

### 新增
- MP3 在线播放 `<audio controls />`
- MP3/TXT/MP4 下载
- 视频生成可选 (generate_video 开关)，默认关闭

### 语言控制
- 支持 11 种语言: zh/en/ja/ko/fr/de/es/pt/ru/th/vi
- 中文 prompt 需加强制指令: "歌词必须使用汉字书写，不要使用拼音"
- `vocal_language` 参数同步传递给 acestep

## 常见问题

### Backend 500 — 数据库列不存在
旧 `codi.db` 与新 schema 不匹配。删除数据库文件重启即可。

### Proxy 干扰 (httpx)
```python
# 必须在导入 httpx 之前清除
for _key in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"):
    os.environ.pop(_key, None)
```

### acestep 首次请求慢
模型加载到 GPU 需要 1-3 分钟，后续请求正常。

### vite 端口被占用
Vite 会自动切换端口。注意 proxy target 不变，不需修改。
