from datetime import datetime, timezone
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .db import Base

def now_utc():
    return datetime.now(timezone.utc)

class Video(Base):
    __tablename__ = "videos"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    url: Mapped[str] = mapped_column(String(1000), unique=True, index=True)
    platform_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    creator: Mapped[str | None] = mapped_column(String(200), nullable=True)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    transcript: Mapped[str | None] = mapped_column(Text, nullable=True)
    collector: Mapped[str] = mapped_column(String(30), default="official")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    snapshots: Mapped[list["Snapshot"]] = relationship(back_populates="video", cascade="all, delete-orphan", order_by="Snapshot.captured_at")

class Snapshot(Base):
    __tablename__ = "snapshots"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    video_id: Mapped[int] = mapped_column(ForeignKey("videos.id", ondelete="CASCADE"), index=True)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    views: Mapped[int | None] = mapped_column(Integer, nullable=True)
    likes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    comments: Mapped[int | None] = mapped_column(Integer, nullable=True)
    shares: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source: Mapped[str] = mapped_column(String(30))
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)
    video: Mapped["Video"] = relationship(back_populates="snapshots")
