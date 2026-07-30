# ScamShield — 詐欺サイト撲滅アプリ（Web MVP）

URL危険度判定・詐欺特徴検知・匿名通報・被害防止ガイドを一体化した被害予防Webサービスです。

## 機能

- URL危険度判定（スコア / high·medium·low / 理由）
- ドメイン・文言ヒューリスティック（HTTPS、疑わしいTLD、タイポスクワット、支払い誘導など）
- 匿名通報 + カテゴリ集計ダッシュボード
- 啓発コンテンツ（判定結果から関連ガイドへ誘導）
- レート制限・セキュリティヘッダ・免責表示

## 起動

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

ブラウザ: http://127.0.0.1:8000

## API

| Method | Path | 説明 |
|--------|------|------|
| GET | `/health` | ヘルスチェック |
| POST | `/api/check-url` | URL判定 |
| POST | `/api/reports` | 通報 |
| GET | `/api/reports/stats` | 通報統計 |
| GET | `/api/education` | 啓発一覧 |
| GET | `/api/education/{slug}` | 啓発詳細 |
| GET | `/api/disclaimer` | 免責文 |
| GET | `/metrics` | 監視メトリクス |

## テスト / スモーク

```bash
python -m pytest -q
python scripts/smoke_test.py
```

## 無料枠デプロイ

手順は [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)（Render Free + Docker）。

## 注意

判定結果は補助情報です。最終判断は利用者自身で行ってください。
