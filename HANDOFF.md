# HANDOFF — scam-shield-mvp

更新: 2026-09-21

## 正本

`C:\Users\cz7\Projects\scam-shield-mvp`

## Remote

https://github.com/YMD-yamada/scam-shield-mvp （branch: `main`）

## 目的

詐欺サイト被害予防の Web MVP。URL判定・ヒューリスティック・匿名通報・啓発。

## 現状

- FastAPI + SQLite + 静的フロントを単一リポジトリで実装済み
- 主要API: `/api/check-url`, `/api/reports`, `/api/education`, `/metrics`
- テスト: `tests/test_api.py` + `tests/test_detection.py`（14 passed）
- スモーク: `scripts/smoke_test.py` OK
- デプロイ雛形: `Dockerfile`, `render.yaml`, `docs/DEPLOYMENT.md`
- GitHub push 済み。Render 公開はダッシュボード操作が必要（無料枠 Blueprint）

## 起動

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## 次アクション

0. PR #1（detection ユニットテスト追加）のレビュー・マージ
1. Render Free Blueprint で公開（`docs/DEPLOYMENT.md`）
2. `ALLOW_ORIGINS` を本番URLに固定
3. 公開URL確定後、personal-site / ymd-portfolio へ掲載

## 非スコープ

駅マッチ・ボットユーザー・他アプリのコード混在はしない。
