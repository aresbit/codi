"""
数据模型 — SQLite
"""

from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, DateTime, Text, Enum as SAEnum
from sqlalchemy.orm import DeclarativeBase
import enum


class Base(DeclarativeBase):
    pass


class OrderStatus(str, enum.Enum):
    pending = "pending"            # 待生成
    generating = "generating"      # 生成中
    completed = "completed"        # 完成，可下载
    failed = "failed"              # 生成失败


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
    generate_video = Column(String(5), default="true")  # "true"/"false"

    # 生成结果
    lyrics = Column(Text, default="")
    audio_url = Column(String(512), default="")
    video_url = Column(String(512), default="")
    error_message = Column(Text, default="")

    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
