"""
Codi API — AI 定制音乐
FastAPI 后端主入口
"""

import uuid
import os
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select

from config import STYLES, OCCASIONS, AUDIENCES
from models import Base, Order, OrderStatus
from generator import build_music_prompt, generate_with_ace_step
from video import compose_video

# ---- 初始化 ----
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./codi.db")
engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

OUTPUT_DIR = Path(os.getenv("CODI_OUTPUT", "./output"))
OUTPUT_DIR.mkdir(exist_ok=True)

app = FastAPI(title="Codi", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# ---- Pydantic 模型 ----

class CreateOrderRequest(BaseModel):
    audience: str      # lover/friend/family/self/colleague
    occasion: str      # love/proposal/wedding/birthday/graduation/missing/encourage/thanks/new_year
    personal_note: str = ""
    style: str         # mountain_song/folk/pop_ballad/rock/rap/rnb/chinese_style/light_music
    language: str = "zh"
    generate_video: bool = False  # 默认可选，无需等待视频合成
    exact_lyrics: str = ""       # 用户提供的精确歌词（可选），传入后将使用 format 模式不修改


class CreateOrderResponse(BaseModel):
    order_id: str


class OrderStatusResponse(BaseModel):
    order_id: str
    status: str
    audio_url: str | None
    video_url: str | None
    lyrics: str | None
    error_message: str | None


# ---- API 路由 ----

@app.get("/api/styles")
async def list_styles():
    """获取可用风格列表"""
    return {"styles": STYLES}


@app.get("/api/occasions")
async def list_occasions():
    """获取可用场景列表"""
    return {"occasions": [
        {"key": k, "label": v} for k, v in OCCASIONS.items()
    ]}


@app.get("/api/audiences")
async def list_audiences():
    """获取受众选项"""
    return {"audiences": [
        {"key": k, "label": v} for k, v in AUDIENCES.items()
    ]}


@app.post("/api/orders", response_model=CreateOrderResponse)
async def create_order(req: CreateOrderRequest, background_tasks: BackgroundTasks):
    """创建订单并立即开始生成"""
    # 验证输入
    if req.style not in STYLES:
        raise HTTPException(400, f"不支持的风格: {req.style}")
    if req.audience not in AUDIENCES:
        raise HTTPException(400, f"不支持的受众: {req.audience}")

    order_id = datetime.utcnow().strftime("%Y%m%d%H%M%S") + uuid.uuid4().hex[:8]

    order = Order(
        id=order_id,
        status=OrderStatus.generating,
        audience=req.audience,
        occasion=req.occasion,
        personal_note=req.personal_note,
        style=req.style,
        language=req.language,
        generate_video="true" if req.generate_video else "false",
    )

    async with AsyncSessionLocal() as session:
        session.add(order)
        await session.commit()

    # 后台异步生成
    background_tasks.add_task(_generate_song, order_id, req.exact_lyrics)
    return CreateOrderResponse(order_id=order_id)


@app.get("/api/orders/{order_id}", response_model=OrderStatusResponse)
async def get_order_status(order_id: str):
    """查询订单状态 & 结果"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Order).where(Order.id == order_id)
        )
        order = result.scalar_one_or_none()
        if not order:
            raise HTTPException(404, "订单不存在")

        return OrderStatusResponse(
            order_id=order.id,
            status=order.status.value,
            audio_url=order.audio_url,
            video_url=order.video_url,
            lyrics=order.lyrics,
            error_message=order.error_message,
        )


async def _generate_song(order_id: str, exact_lyrics: str = ""):
    """
    完整生成流程：
    Prompt构建 → ACE-Step生成 → MP4视频合成
    exact_lyrics: 用户提供的精确歌词（可选），传参后将使用 format 模式不修改
    """
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Order).where(Order.id == order_id))
        order = result.scalar_one_or_none()
        if not order:
            return

        order_dir = OUTPUT_DIR / order_id
        order_dir.mkdir(exist_ok=True)

        try:
            # 1. 构建 prompt
            prompt_data = build_music_prompt(
                exact_lyrics=exact_lyrics,
                audience_key=order.audience,
                occasion_key=order.occasion,
                personal_note=order.personal_note,
                style_key=order.style,
                language=order.language,
            )

            # 2. 调用 ACE-Step 生成音乐
            gen_result = await generate_with_ace_step(prompt_data, order_id)
            audio_path = gen_result["audio_path"]
            lyrics = gen_result["lyrics_text"]

            order.lyrics = lyrics

            # 3. 保存音频结果
            audio_filename = os.path.basename(audio_path)
            order.audio_url = f"/api/files/{order_id}/{audio_filename}"

            # 4. 可选合成 MP4
            if order.generate_video == "true":
                style_name = prompt_data["style_name"]
                video_path = compose_video(audio_path, lyrics, order_id, style_name)
                order.video_url = f"/api/files/{order_id}/{order_id}.mp4"

            order.status = OrderStatus.completed
            order.completed_at = datetime.utcnow()

        except Exception as e:
            order.status = OrderStatus.failed
            order.error_message = str(e)

        await session.commit()


@app.get("/api/files/{order_id}/{filename}")
async def serve_file(order_id: str, filename: str):
    """文件下载"""
    file_path = OUTPUT_DIR / order_id / filename
    if not file_path.exists():
        raise HTTPException(404, "文件不存在")
    return FileResponse(file_path)


# ---- 健康检查 ----

@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}


# ---- 启动 ----

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
