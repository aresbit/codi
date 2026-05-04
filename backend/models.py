"""
数据模型 — SQLite (MVP)，后续可切换 PostgreSQL
"""

from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, DateTime, Text, Enum as SAEnum
from sqlalchemy.orm import DeclarativeBase
import enum


class Base(DeclarativeBase):
    pass


class OrderStatus(str, enum.Enum):
    pending = "pending"            # 待支付
    paid = "paid"                  # 已支付，排队生成
    generating = "generating"      # 生成中
    completed = "completed"        # 完成，可下载
    failed = "failed"              # 生成失败


class PriceTier(str, enum.Enum):
    basic = "basic"           # ¥5: MP4 + 歌词
    premium = "premium"       # ¥8: MP4 + 歌词 + 曲谱


class Order(Base):
    __tablename__ = "orders"

    id = Column(String(32), primary_key=True)
    status = Column(SAEnum(OrderStatus), default=OrderStatus.pending, nullable=False)

    # 用户三步输入
    audience = Column(String(32), nullable=False)
    occasion = Column(String(32), nullable=False)
    personal_note = Column(Text, default="")
    style = Column(String(32), nullable=False)
    language = Column(String(8), default="zh")

    # 价格
    tier = Column(SAEnum(PriceTier), nullable=False)
    price = Column(Float, nullable=False)

    # 微信支付
    wx_openid = Column(String(64), default="")
    wx_prepay_id = Column(String(64), default="")
    wx_transaction_id = Column(String(64), default="")

    # 生成结果
    lyrics = Column(Text, default="")
    audio_url = Column(String(512), default="")
    video_url = Column(String(512), default="")
    sheet_music_url = Column(String(512), default="")
    error_message = Column(Text, default="")

    created_at = Column(DateTime, default=datetime.utcnow)
    paid_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
