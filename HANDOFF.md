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

1. **人間の作業**: Render Free Blueprint で公開（手順は `docs/DEPLOYMENT.md`）
   - ダッシュボードでの GitHub 連携とログインが必要なため Claude Code では実施できない
   - プランが **Free** になっているかを必ず目視確認（`plan` 省略時の Render 既定は有料）
2. 公開後に `ALLOW_ORIGINS` を本番 URL に設定して再デプロイ
3. 公開URL確定後、personal-site / ymd-portfolio へ掲載

## セッション記録

### 2026-09-21 Claude Code（2）Render 設定修正

- PR #2 マージ済み（`c1f09a7`）/ PR #3 マージ済み（`cdd548a`）
- `render.yaml`: `plan: free` を明記。**未指定だと Render は `0.5c-512mb`（有料）を割り当てる**ため、
  そのままデプロイすると課金されるところだった。
- `Dockerfile`: ポート直書き 8000 → `${PORT:-8000}`。Render は `PORT`（既定 10000）を注入する。
- `Dockerfile`: uvicorn に `--proxy-headers --forwarded-allow-ips='*'` を追加。
  前回「未対応」としていたレート制限の IP 問題を解消。ローカルで検証済み
  （`X-Forwarded-For: 203.0.113.9` がクライアント IP として記録されることを確認）。
- `docs/DEPLOYMENT.md`: 現状に合わせて更新。**Free はファイルシステムが揮発性で通報データが永続しない**
  ことを明記（永続化には有料プラン + ディスク、または外部 Postgres が必要）。
- 前回「未対応」の CORS `allow_credentials=True` は、`ALLOW_ORIGINS` に `*` を入れない運用で回避する方針。
- PR #3: CI に `docker` ジョブを追加。開発機に Docker が無くイメージを検証できなかったため、
  CI 上で build → `PORT=10000` で起動 → `/health` 確認 → `X-Forwarded-For` がクライアント IP として
  記録されることを検証する。将来 `--proxy-headers` が外れたら CI が落ちる。
  実行結果: image build OK、`{"ok":true,...}` 応答 OK、forwarded IP 検出 OK。

### 2026-09-21 Claude Code（1）テスト追加

- 追加: `tests/test_detection.py`（`normalize_url` / `evaluate_url` のユニットテスト 9 件）。`app/` は無変更。
- 改名: `CURSOR_HANDOFF.md` → `HANDOFF.md`（`git mv`。旧名の参照は repo 内に無し）。
- 検証: `py -3 -m pytest -q` → 14 passed。GitHub Actions `test` → pass。
- PR #1 を `main` へマージ済み（merge commit `4e8ab2b`、2026-09-21）。作業ブランチは削除済み。
- マージ操作は Claude Code の auto mode が「Merge Without Review」として拒否したため、人間が実施。
  以降は Claude Code が実施してよい旨の指示あり（`gh pr merge` の許可ルールが入るまでは同じ拒否が出る）。
- 未対応（別件・コード未変更）:
  - `app/main.py` のレート制限が `request.client.host` 依存。プロキシ配下だと全員が同一 IP に集約される（`Dockerfile` の uvicorn に `--proxy-headers` 無し）。
  - `app/main.py` の CORS が `allow_credentials=True`。本番で `ALLOW_ORIGINS` に `*` を入れないこと。

## 非スコープ

駅マッチ・ボットユーザー・他アプリのコード混在はしない。
