"""
SongCraft API — 泛音乐定制服务
FastAPI 后端主入口
"""

import uuid
import os
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select

from config import STYLES, OCCASIONS, AUDIENCES, PRICE_TIER_BASIC, PRICE_TIER_PREMIUM
from models import Base, Order, OrderStatus, PriceTier
from generator import build_music_prompt, generate_with_ace_step
from notation import generate_sheet_music
from video import compose_video

# ---- 初始化 ----
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./songcraft.db")
engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

OUTPUT_DIR = Path(os.getenv("SONGCRAFT_OUTPUT", "./output"))
OUTPUT_DIR.mkdir(exist_ok=True)

app = FastAPI(title="SongCraft", version="0.1.0")


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
    tier: str = "basic"  # basic / premium


class CreateOrderResponse(BaseModel):
    order_id: str
    price: float
    payment_params: dict | None  # 微信支付调起参数


class OrderStatusResponse(BaseModel):
    order_id: str
    status: str
    price: float
    tier: str
    video_url: str | None
    sheet_music_url: str | None
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
async def create_order(req: CreateOrderRequest, request: Request):
    """
    创建订单：
    1. 用户在三步问卷后提交
    2. 生成订单，返回微信支付参数
    """
    # 验证输入
    if req.style not in STYLES:
        raise HTTPException(400, f"不支持的风格: {req.style}")
    if req.audience not in AUDIENCES:
        raise HTTPException(400, f"不支持的受众: {req.audience}")
    if req.tier not in ("basic", "premium"):
        raise HTTPException(400, f"不支持的套餐: {req.tier}")

    order_id = datetime.utcnow().strftime("%Y%m%d%H%M%S") + uuid.uuid4().hex[:8]
    price = PRICE_TIER_PREMIUM if req.tier == "premium" else PRICE_TIER_BASIC

    order = Order(
        id=order_id,
        status=OrderStatus.pending,
        audience=req.audience,
        occasion=req.occasion,
        personal_note=req.personal_note,
        style=req.style,
        language=req.language,
        tier=PriceTier(req.tier),
        price=price,
    )

    async with AsyncSessionLocal() as session:
        session.add(order)
        await session.commit()

    # 获取支付参数（MVP阶段如果没配微信商户，返回模拟数据）
    payment_params = None
    try:
        from payment import create_jsapi_order
        openid = request.headers.get("X-WX-OpenID", "")
        desc = f"AI定制歌曲 · {STYLES[req.style]['name']}"
        payment_params = await create_jsapi_order(order_id, req.tier, openid, desc)
    except Exception:
        # MVP 回退：直接标记为已支付（测试用）
        payment_params = {"mode": "test", "order_id": order_id}

    return CreateOrderResponse(
        order_id=order_id,
        price=price,
        payment_params=payment_params,
    )


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
            price=order.price,
            tier=order.tier.value,
            video_url=order.video_url,
            sheet_music_url=order.sheet_music_url,
            lyrics=order.lyrics,
            error_message=order.error_message,
        )


@app.post("/api/orders/{order_id}/generate")
async def trigger_generation(order_id: str, background_tasks: BackgroundTasks):
    """
    触发歌曲生成（支付成功后调用）。
    异步处理：后台生成 → 完成后更新订单状态。
    """
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Order).where(Order.id == order_id)
        )
        order = result.scalar_one_or_none()
        if not order:
            raise HTTPException(404, "订单不存在")

        if order.status != OrderStatus.pending:
            raise HTTPException(400, f"订单状态不正确: {order.status}")

        order.status = OrderStatus.generating
        await session.commit()

    # 后台异步生成
    background_tasks.add_task(_generate_song, order_id)
    return {"status": "generating"}


async def _generate_song(order_id: str):
    """
    完整生成流程：
    Prompt构建 → ACE-Step生成 → 曲谱渲染 → 视频合成
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

            # 3. 曲谱生成（仅 premium）
            sheet_pngs = None
            if order.tier == PriceTier.premium:
                sheet_pngs = generate_sheet_music(audio_path, order_id)

            # 4. 合成 MP4
            style_name = prompt_data["style_name"]
            video_path = compose_video(audio_path, lyrics, sheet_pngs,
                                       order_id, style_name)

            # 5. 保存结果
            order.video_url = f"/api/files/{order_id}/{order_id}.mp4"
            if sheet_pngs:
                order.sheet_music_url = f"/api/files/{order_id}/sheet_music.png"
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


# ---- 微信支付回调 ----

@app.post("/api/pay/notify")
async def payment_notify(request: Request):
    """微信支付异步通知"""
    body = await request.body()
    signature = request.headers.get("Wechatpay-Signature", "")
    serial = request.headers.get("Wechatpay-Serial", "")
    timestamp = request.headers.get("Wechatpay-Timestamp", "")
    nonce = request.headers.get("Wechatpay-Nonce", "")

    from payment import verify_payment_notification
    result = await verify_payment_notification(body, signature, serial,
                                               timestamp, nonce)
    if not result:
        return {"code": "FAIL", "message": "签名验证失败"}

    order_id = result["order_id"]
    transaction_id = result["transaction_id"]

    async with AsyncSessionLocal() as session:
        r = await session.execute(select(Order).where(Order.id == order_id))
        order = r.scalar_one_or_none()
        if order:
            order.status = OrderStatus.paid
            order.wx_transaction_id = transaction_id
            order.paid_at = datetime.utcnow()
            await session.commit()

    return {"code": "SUCCESS"}


# ---- 健康检查 ----

@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}


# ---- 启动 ----

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
