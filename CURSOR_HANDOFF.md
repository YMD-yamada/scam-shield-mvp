# CURSOR_HANDOFF — scam-shield-mvp

更新: 2026-07-30

## 正本

`C:\Users\cz7\Projects\scam-shield-mvp`

## 目的

詐欺サイト被害予防の Web MVP。URL判定・ヒューリスティック・匿名通報・啓発。

## 現状

- FastAPI + SQLite + 静的フロントを単一リポジトリで実装済み
- 主要API: `/api/check-url`, `/api/reports`, `/api/education`, `/metrics`
- テスト: `tests/test_api.py`
- デプロイ雛形: `Dockerfile`, `render.yaml`, `docs/DEPLOYMENT.md`

## 起動

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## 次アクション

1. GitHub リポジトリへ push（未設定なら新規作成）
2. Render Free Blueprint で公開
3. `ALLOW_ORIGINS` を本番URLに固定
4. 公開後、personal-site / ymd-portfolio へ掲載（公開URL確定後）

## 非スコープ（このリポではやらない）

駅マッチ・ボットユーザー・他アプリのコード混在はしない。
