"""Lightweight smoke: import app + exercise core API paths."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient

from app.main import app


def run() -> None:
    client = TestClient(app)
    health = client.get("/health").json()
    check = client.post(
        "/api/check-url",
        json={"url": "http://amaz0n-support-verify.xyz", "page_text": "至急 verify password"},
    ).json()
    report = client.post(
        "/api/reports",
        json={
            "url": check["normalized_url"],
            "category": "phishing",
            "comment": "smoke",
            "reporter_hash": "smoke-runner",
        },
    ).json()
    stats = client.get("/api/reports/stats").json()
    education = client.get("/api/education").json()
    metrics = client.get("/metrics").json()
    print(
        {
            "health": health,
            "risk_level": check.get("risk_level"),
            "report_status": report.get("status"),
            "report_total": stats.get("total"),
            "education_items": len(education.get("items", [])),
            "metrics": metrics,
        }
    )


if __name__ == "__main__":
    run()
