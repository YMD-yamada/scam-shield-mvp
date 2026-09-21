# ScamShield デプロイ（無料枠）

## 1. GitHub

作成・push 済み: https://github.com/YMD-yamada/scam-shield-mvp

`main` に push すると Render が自動で再デプロイします（`render.yaml` の `autoDeploy: true`）。

## 2. Render Free

1. https://dashboard.render.com/ にログイン
2. `New +` → `Blueprint`
3. GitHub リポジトリ `YMD-yamada/scam-shield-mvp` を連携し `render.yaml` を読み込む
4. サービス名 `scam-shield-mvp` / プラン **Free** を確認
   - `render.yaml` に `plan: free` を明記済み。ここが `0.5c-512mb` 等になっていたら
     課金対象なので中止して確認すること（`plan` を省略した場合の Render 既定は有料）
5. 環境変数
   - `ALLOW_ORIGINS` … Blueprint では `sync: false` にしているのでダッシュボードで手入力する。
     デプロイ後に確定する `https://<service>.onrender.com` を設定する
   - `API_RATE_LIMIT_PER_MIN` = `60`（`render.yaml` で設定済み）
6. デプロイ後の URL を控え、`ALLOW_ORIGINS` に反映して再デプロイ

> Free プランは一定時間アクセスがないとスリープします。初回アクセスで数十秒かかることがあります。

### 無料枠の制約（把握しておくこと）

- **通報データは永続しません。** Free インスタンスのファイルシステムは揮発性で、
  デプロイ・再起動・スリープ復帰のたびに SQLite ファイル `scam_shield.db` が消えます。
  通報を貯め続けたい場合は有料プラン + 永続ディスク、または外部 Postgres が必要です。
- ポートは Render が `PORT`（既定 10000）で指定します。`Dockerfile` は
  `${PORT:-8000}` を見るので、ローカルでは 8000 のまま動きます。
- `--proxy-headers` を付けています。これが無いと Render のプロキシ経由で
  `request.client.host` がプロキシの IP になり、レート制限が全利用者で共有されて
  正しく機能しません。

## 3. 疎通チェック

デプロイ後、`<URL>` を実際のサービス URL に置き換えて実行します。

```bash
curl -s <URL>/health
curl -s -X POST <URL>/api/check-url -H "Content-Type: application/json" -d "{\"url\":\"http://amaz0n-verify-login.xyz\",\"page_text\":\"urgent verify\"}"
curl -s <URL>/metrics
```

- `GET /health` → `{"ok": true, ...}`
- Web UI で URL 判定 → 通報 → ガイド表示
- `GET /metrics` でカウンタ増加を確認

## 4. 運用（無料枠）

1. 週1で `GET /api/reports/stats` を確認
2. 誤報・悪用通報を目視で整理
3. 通報が多いパターンに検出ルールを追加
4. CI が緑のときだけ本番反映
