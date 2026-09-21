"""スコアリング中核 app.detection のユニットテスト。"""

import pytest

from app.detection import evaluate_url, normalize_url


def test_normalize_url_adds_scheme_and_lowercases_domain():
    normalized, domain = normalize_url("Example.COM/Path")
    assert normalized == "http://Example.COM/Path"
    assert domain == "example.com"


def test_normalize_url_keeps_query_and_defaults_empty_path():
    normalized, domain = normalize_url("https://example.com?a=1")
    assert normalized == "https://example.com/?a=1"
    assert domain == "example.com"


def test_normalize_url_rejects_unparsable_input():
    with pytest.raises(ValueError):
        normalize_url("   ")


def test_clean_https_url_is_low_risk():
    result = evaluate_url("https://www.example.org/")
    assert result.risk_score == 0
    assert result.risk_level == "low"
    assert result.reasons == ["現時点で顕著な危険シグナルは検出されませんでした"]


def test_http_and_ip_host_raise_score():
    result = evaluate_url("http://192.168.0.1/")
    assert result.domain == "192.168.0.1"
    assert result.risk_level == "medium"
    assert any("HTTPS未使用" in reason for reason in result.reasons)
    assert any("IP直指定" in reason for reason in result.reasons)


def test_blacklisted_domain_is_high_risk():
    result = evaluate_url("https://secure-wallet-check.com/")
    assert result.risk_level == "high"
    assert any("ブラックリスト" in reason for reason in result.reasons)


def test_typosquat_of_trusted_brand_is_flagged():
    result = evaluate_url("https://amaz0n.com/")
    assert any("タイポスクワット" in reason for reason in result.reasons)


def test_report_count_and_recent_sighting_increase_score():
    baseline = evaluate_url("https://neutral-domain.example/")
    reported = evaluate_url(
        "https://neutral-domain.example/",
        report_count=3,
        domain_seen_recently=True,
    )
    assert reported.risk_score > baseline.risk_score
    assert any("通報が3件" in reason for reason in reported.reasons)
    assert any("最近観測された" in reason for reason in reported.reasons)


def test_score_is_capped_at_100():
    result = evaluate_url(
        "http://login-security-update.top/verify",
        page_text="urgent verify password wallet giftcard 送金 お問い合わせ不可",
        report_count=100,
        domain_seen_recently=True,
    )
    assert result.risk_score == 100
    assert result.risk_level == "high"
