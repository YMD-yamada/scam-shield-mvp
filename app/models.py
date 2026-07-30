from datetime import UTC, datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


class UrlScanLog(Base):
    __tablename__ = "url_scan_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    url: Mapped[str] = mapped_column(String(800), index=True)
    domain: Mapped[str] = mapped_column(String(255), index=True)
    risk_score: Mapped[int] = mapped_column(Integer)
    risk_level: Mapped[str] = mapped_column(String(20), index=True)
    reasons: Mapped[str] = mapped_column(Text, default="")
    scanned_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)


class ScamReport(Base):
    __tablename__ = "scam_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    url: Mapped[str] = mapped_column(String(800), index=True)
    normalized_domain: Mapped[str] = mapped_column(String(255), index=True)
    category: Mapped[str] = mapped_column(String(60), index=True)
    comment: Mapped[str] = mapped_column(Text, default="")
    reporter_hash: Mapped[str] = mapped_column(String(120), index=True, default="anonymous")
    status: Mapped[str] = mapped_column(String(20), index=True, default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
