from __future__ import annotations

from collections import defaultdict, deque
from datetime import UTC, datetime, timedelta
import logging
import os
from pathlib import Path
import time

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db import Base, engine, get_db
from app.detection import evaluate_url, normalize_url
from app.models import ScamReport, UrlScanLog
from app.schemas import ScamReportCreate, ScamReportResponse, UrlCheckRequest, UrlCheckResponse

Base.metadata.create_all(bind=engine)

logger = logging.getLogger("scam-shield")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

app = FastAPI(title="詐欺サイト撲滅アプリ API", version="1.0.0")
allow_origins = os.getenv("ALLOW_ORIGINS", "http://localhost:8000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[x.strip() for x in allow_origins if x.strip()],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)

DISCLAIMER = (
    "本サービスの危険度判定は被害防止を補助する情報です。"
    "最終的なアクセス可否は利用者ご自身でご判断ください。"
)
EDUCATION_CONTENT = [
    {
        "slug": "urgent-scam",
        "title": "緊急性をあおる詐欺の見分け方",
        "category": "心理誘導",
        "summary": "至急対応・アカウント停止通知を装う文面への対処法。",
        "checklist": [
            "本文中リンクではなく公式アプリやブックマークから入り直す",
            "時間制限を強調されたら一度離れて第三者に相談する",
            "個人情報や認証コードの入力前にURLを再確認する",
        ],
    },
    {
        "slug": "payment-scam",
        "title": "不自然な支払い誘導への対処",
        "category": "決済",
        "summary": "ギフトカードや暗号資産送金を求める誘導の対策。",
        "checklist": [
            "ギフトカード番号の送付依頼は詐欺を疑う",
            "請求元企業を公式窓口で確認する",
            "送金前に通報して証拠スクリーンショットを保存する",
        ],
    },
    {
        "slug": "impersonation",
        "title": "なりすましサイトのチェックポイント",
        "category": "なりすまし",
        "summary": "有名ブランドや銀行を装う偽サイトの見分け方。",
        "checklist": [
            "ドメインの綴りを公式サイトと一字一句比較する",
            "HTTPSだけでなく証明書の発行元も確認する",
            "公式アプリからのログインを優先する",
        ],
    },
]

REQUEST_LIMIT = int(os.getenv("API_RATE_LIMIT_PER_MIN", "60"))
REQUEST_WINDOW = timedelta(minutes=1)
REQUEST_BUCKET: dict[str, deque[datetime]] = defaultdict(deque)
REPORT_RATE_LIMIT: dict[str, deque[datetime]] = defaultdict(deque)
METRICS = {
    "check_url_calls": 0,
    "report_create_calls": 0,
    "request_blocked": 0,
    "error_count": 0,
    "check_url_latency_ms_last": 0,
}


@app.get("/health")
def health():
    return {"ok": True, "service": "scam-shield", "version": app.version}


@app.exception_handler(Exception)
async def global_exception_handler(_: Request, exc: Exception):
    METRICS["error_count"] += 1
    logger.exception("Unhandled exception: %s", exc)
    return JSONResponse(status_code=500, content={"detail": "internal server error"})


@app.middleware("http")
async def security_middleware(request: Request, call_next):
    ip = request.client.host if request.client else "unknown"
    now = datetime.now(UTC)
    bucket = REQUEST_BUCKET[ip]
    while bucket and now - bucket[0] > REQUEST_WINDOW:
        bucket.popleft()
    if len(bucket) >= REQUEST_LIMIT:
        METRICS["request_blocked"] += 1
        return JSONResponse(status_code=429, content={"detail": "rate limit exceeded"})
    bucket.append(now)

    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'"
    )
    return response


@app.get("/api/disclaimer")
def get_disclaimer():
    return {"text": DISCLAIMER}


@app.post("/api/check-url", response_model=UrlCheckResponse)
def check_url(payload: UrlCheckRequest, db: Session = Depends(get_db)):
    started = time.perf_counter()
    METRICS["check_url_calls"] += 1
    try:
        normalized_url, domain = normalize_url(payload.url)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    report_count = db.query(ScamReport).filter(ScamReport.normalized_domain == domain).count()
    recent_window = datetime.now(UTC) - timedelta(days=7)
    recently_seen = (
        db.query(UrlScanLog)
        .filter(UrlScanLog.domain == domain, UrlScanLog.scanned_at >= recent_window)
        .first()
        is not None
    )
    result = evaluate_url(
        raw_url=normalized_url,
        page_text=payload.page_text,
        report_count=report_count,
        domain_seen_recently=recently_seen,
    )
    db.add(
        UrlScanLog(
            url=result.normalized_url,
            domain=result.domain,
            risk_score=result.risk_score,
            risk_level=result.risk_level,
            reasons="|".join(result.reasons),
        )
    )
    db.commit()
    METRICS["check_url_latency_ms_last"] = int((time.perf_counter() - started) * 1000)
    return UrlCheckResponse(**result.__dict__)


@app.post("/api/reports", response_model=ScamReportResponse)
def create_report(payload: ScamReportCreate, db: Session = Depends(get_db)):
    METRICS["report_create_calls"] += 1
    try:
        normalized_url, domain = normalize_url(payload.url)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    reporter = payload.reporter_hash or "anonymous"
    now = datetime.now(UTC)
    report_bucket = REPORT_RATE_LIMIT[reporter]
    while report_bucket and now - report_bucket[0] > timedelta(minutes=10):
        report_bucket.popleft()
    if len(report_bucket) >= 5:
        raise HTTPException(status_code=429, detail="通報上限に達しました。時間を空けて再試行してください。")

    duplicate_cutoff = now - timedelta(minutes=30)
    duplicate = (
        db.query(ScamReport)
        .filter(
            ScamReport.normalized_domain == domain,
            ScamReport.reporter_hash == reporter,
            ScamReport.created_at >= duplicate_cutoff,
        )
        .first()
    )
    if duplicate:
        return ScamReportResponse(
            id=duplicate.id,
            status="duplicate",
            created_at=duplicate.created_at.isoformat(),
        )

    report = ScamReport(
        url=normalized_url,
        normalized_domain=domain,
        category=payload.category,
        comment=payload.comment,
        reporter_hash=reporter,
        status="pending",
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    report_bucket.append(now)
    return ScamReportResponse(id=report.id, status=report.status, created_at=report.created_at.isoformat())


@app.get("/api/reports/stats")
def report_stats(db: Session = Depends(get_db)):
    per_category = (
        db.query(ScamReport.category, func.count(ScamReport.id))
        .group_by(ScamReport.category)
        .order_by(func.count(ScamReport.id).desc())
        .all()
    )
    latest = db.query(ScamReport).order_by(ScamReport.created_at.desc()).limit(5).all()
    return {
        "total": db.query(ScamReport).count(),
        "by_category": [{"category": category, "count": count} for category, count in per_category],
        "latest": [
            {
                "id": row.id,
                "url": row.url,
                "category": row.category,
                "status": row.status,
                "created_at": row.created_at.isoformat(),
            }
            for row in latest
        ],
    }


@app.get("/api/education")
def list_education(category: str = Query("", description="カテゴリでフィルタ")):
    if not category:
        return {"items": EDUCATION_CONTENT}
    return {"items": [item for item in EDUCATION_CONTENT if item["category"] == category]}


@app.get("/api/education/{slug}")
def get_education(slug: str):
    for item in EDUCATION_CONTENT:
        if item["slug"] == slug:
            return item
    raise HTTPException(status_code=404, detail="content not found")


@app.get("/metrics")
def metrics():
    return METRICS


FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
