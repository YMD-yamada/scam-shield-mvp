"""URL reputation + scam heuristics scoring."""

from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher
import re
from urllib.parse import urlparse

SUSPICIOUS_TLDS = {"xyz", "top", "click", "gq", "tk", "work", "fit", "buzz", "icu", "cfd"}
BLACKLISTED_DOMAINS = {
    "secure-wallet-check.com",
    "account-verify-center.net",
    "login-security-update.top",
}
TRUSTED_BRANDS = {
    "amazon",
    "rakuten",
    "apple",
    "microsoft",
    "google",
    "line",
    "paypal",
    "bank",
    "mufg",
    "smbc",
}
SUSPICIOUS_KEYWORDS = {
    "urgent",
    "verify",
    "suspend",
    "giftcard",
    "gift-card",
    "crypto",
    "wallet",
    "password",
    "2fa",
    "otp",
    "認証",
    "停止",
    "至急",
    "確認してください",
    "アカウント",
    "振込",
    "ギフトカード",
}
PAYMENT_HEURISTICS = {
    "gift card",
    "giftcard",
    "bitcoin",
    "crypto wallet",
    "wire transfer",
    "送金",
    "仮想通貨",
    "プリペイド",
}
CONTACT_GAP_HINTS = {
    "お問い合わせ不可",
    "電話なし",
    "no phone",
    "contact unavailable",
}


@dataclass
class RiskResult:
    normalized_url: str
    domain: str
    risk_score: int
    risk_level: str
    reasons: list[str]


def normalize_url(raw_url: str) -> tuple[str, str]:
    candidate = raw_url.strip()
    if not candidate.startswith(("http://", "https://")):
        candidate = "http://" + candidate
    parsed = urlparse(candidate)
    if not parsed.hostname:
        raise ValueError("URLを解析できませんでした")
    normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path or '/'}"
    if parsed.query:
        normalized += f"?{parsed.query}"
    return normalized, parsed.hostname.lower()


def _looks_like_ip(host: str) -> bool:
    return bool(re.fullmatch(r"\d{1,3}(\.\d{1,3}){3}", host))


def _looks_like_typosquat(host: str) -> bool:
    host_without_tld = host.split(".")[0]
    for brand in TRUSTED_BRANDS:
        ratio = SequenceMatcher(a=host_without_tld, b=brand).ratio()
        if ratio >= 0.75 and host_without_tld != brand:
            return True
        if brand in host_without_tld and host_without_tld != brand:
            return True
    return False


def evaluate_url(
    raw_url: str,
    page_text: str = "",
    report_count: int = 0,
    domain_seen_recently: bool = False,
) -> RiskResult:
    normalized_url, domain = normalize_url(raw_url)
    parsed = urlparse(normalized_url)
    reasons: list[str] = []
    score = 0

    if parsed.scheme != "https":
        score += 20
        reasons.append("HTTPS未使用のため盗聴・改ざんリスクがあります")
    if _looks_like_ip(domain):
        score += 25
        reasons.append("ドメインがIP直指定です")
    tld = domain.split(".")[-1] if "." in domain else ""
    if tld in SUSPICIOUS_TLDS:
        score += 15
        reasons.append("悪用報告が比較的多いTLDです")
    if domain in BLACKLISTED_DOMAINS:
        score += 60
        reasons.append("既知のブラックリストに一致しました")
    if _looks_like_typosquat(domain):
        score += 20
        reasons.append("有名サービスを装うタイポスクワットの疑いがあります")
    if any(keyword in normalized_url.lower() for keyword in SUSPICIOUS_KEYWORDS):
        score += 10
        reasons.append("URL文字列に詐欺で使われやすい語句があります")

    text_lower = page_text.lower()
    keyword_hits = [k for k in SUSPICIOUS_KEYWORDS if k in text_lower]
    if len(keyword_hits) >= 2:
        score += min(25, len(keyword_hits) * 4)
        reasons.append("ページ文面に不審な誘導語が複数含まれます")
    payment_hits = [k for k in PAYMENT_HEURISTICS if k in text_lower]
    if payment_hits:
        score += 15
        reasons.append("不自然な支払い誘導（ギフトカード/暗号資産等）の兆候があります")
    if any(hint in text_lower for hint in CONTACT_GAP_HINTS):
        score += 10
        reasons.append("連絡先が不明瞭または問い合わせ不可の記述があります")

    if report_count > 0:
        score += min(30, report_count * 6)
        reasons.append(f"同一ドメインに対して通報が{report_count}件あります")
    if domain_seen_recently:
        score += 8
        reasons.append("最近観測されたドメインのため注意が必要です")

    score = min(100, score)
    if score >= 70:
        level = "high"
    elif score >= 40:
        level = "medium"
    else:
        level = "low"

    if not reasons:
        reasons.append("現時点で顕著な危険シグナルは検出されませんでした")

    return RiskResult(
        normalized_url=normalized_url,
        domain=domain,
        risk_score=score,
        risk_level=level,
        reasons=reasons,
    )
