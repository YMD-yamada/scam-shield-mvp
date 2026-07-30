from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["service"] == "scam-shield"


def test_check_url_returns_risk_score():
    response = client.post(
        "/api/check-url",
        json={
            "url": "http://amaz0n-verify-login.xyz",
            "page_text": "urgent verify password wallet giftcard 送金",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["risk_score"] >= 40
    assert body["risk_level"] in {"medium", "high"}
    assert body["domain"] == "amaz0n-verify-login.xyz"
    assert len(body["reasons"]) >= 1


def test_report_duplicate_is_deduped():
    payload = {
        "url": "https://fake-payments.example",
        "category": "payment_fraud",
        "comment": "test report",
        "reporter_hash": "tester-x",
    }
    first = client.post("/api/reports", json=payload)
    second = client.post("/api/reports", json=payload)
    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["status"] in {"duplicate", "pending"}


def test_education_and_disclaimer():
    education = client.get("/api/education")
    assert education.status_code == 200
    assert len(education.json()["items"]) >= 2

    detail = client.get("/api/education/payment-scam")
    assert detail.status_code == 200
    assert detail.json()["slug"] == "payment-scam"

    disclaimer = client.get("/api/disclaimer")
    assert disclaimer.status_code == 200
    assert "補助" in disclaimer.json()["text"]


def test_report_stats():
    response = client.get("/api/reports/stats")
    assert response.status_code == 200
    body = response.json()
    assert "total" in body
    assert "by_category" in body
