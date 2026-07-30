# ScamShield デプロイ（無料枠）

## 1. GitHub

1. https://github.com/new でリポジトリ作成（例: `scam-shield-mvp`）
2. ローカルから push

```bash
git add .
git commit -m "Release: scam-shield web MVP"
git branch -M main
git remote add origin <YOUR_REPO_URL>
git push -u origin main
```

## 2. Render Free

1. https://dashboard.render.com/ にログイン
2. `New +` → `Blueprint`
3. GitHub リポジトリを連携し `render.yaml` を読み込む
4. サービス名 `scam-shield-mvp` を確認
5. 環境変数
   - `ALLOW_ORIGINS` = `https://<your-app>.onrender.com`
   - `API_RATE_LIMIT_PER_MIN` = `60`
6. デプロイ後の URL を控える

> Free プランはスリープすることがあります。初回アクセスで数秒かかることがあります。

## 3. 疎通チェック

- `GET /health` → `ok: true`
- Web UI で URL 判定 → 通報 → ガイド表示
- `GET /metrics` でカウンタ増加を確認

## 4. 運用（無料枠）

1. 週1で `GET /api/reports/stats` を確認
2. 誤報・悪用通報を目視で整理
3. 通報が多いパターンに検出ルールを追加
4. CI が緑のときだけ本番反映
