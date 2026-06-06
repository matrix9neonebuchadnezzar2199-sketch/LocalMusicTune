# LocalMusicTune

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Status](https://img.shields.io/badge/Status-Pre--release-orange.svg)](https://github.com/matrix9neonebuchadnezzar2199-sketch/LocalMusicTune/releases)
[![ACE-Step](https://img.shields.io/badge/Engine-ACE--Step%201.5-green.svg)](https://github.com/ace-step/ACE-Step-1.5)

**Windows / Linux 向けのローカル AI 音楽生成ツール。** ブラウザ上の Gradio UI から、プロンプト・ムードプリセット・楽器・BPM を指定して曲を生成します。クラウド API 不要、モデルは Hugging Face からローカルに取得して動作します。

> **現在 v0.3.0（プレリリース）** — Web UI・プロンプト合成・モデルダウンロードまで利用可能です。**ACE-Step による本番推論は v0.4.0 で実装予定**です。現時点の「生成」ボタンは UI 動作確認用のプレースホルダーです。

---

## 特徴

- **完全ローカル** — 生成処理を自分の PC 上で実行（Docker 不要）
- **AMD / NVIDIA 両対応設計** — ROCm（Radeon）を第一級ターゲットに、CUDA も同等にサポート予定
- **直感的な Web UI** — ダークテーマの Gradio インターフェース（[UI モック](./assets/mockup.html) 準拠）
- **7 種類のムードプリセット** — 睡眠・チル・集中・カフェ・ワークアウト・ゲーム・シネマティック
- **ACE-Step 1.5 モデル管理** — Hugging Face からワンクリック DL、保管済みモデルの選択
- **合成プロンプトプレビュー** — UI 上で最終プロンプトをリアルタイム確認

## 動作環境

| 項目 | 要件 |
|------|------|
| OS | Windows 11（推奨）、WSL2 / Linux |
| Python | 3.10 以上 |
| パッケージ管理 | [uv](https://docs.astral.sh/uv/) 推奨 |
| GPU（推奨） | AMD Radeon（ROCm）または NVIDIA（CUDA） |
| ディスク | モデル 1 体あたり約 5〜10 GB の空き容量 |

### VRAM の目安（ACE-Step 1.5）

| モデル | 重み | 最低 VRAM | 推奨 VRAM |
|--------|------|-----------|-----------|
| 標準 (2B) | 約 4.7 GB | 4 GB | 8 GB |
| XL (4B) | 約 9 GB | 12 GB（オフロード時） | 20 GB |
| XL Turbo | 約 9 GB | 12 GB | 16 GB |

VRAM が厳しい Radeon 環境では **標準 (2B)** または **XL Turbo** から始めることを推奨します。詳細は [ACE-Step GPU 互換性ドキュメント](https://github.com/ace-step/ACE-Step-1.5/blob/main/docs/en/GPU_COMPATIBILITY.md) を参照してください。

---

## インストール

### 1. リポジトリの取得

```powershell
git clone https://github.com/matrix9neonebuchadnezzar2199-sketch/LocalMusicTune.git
cd LocalMusicTune
```

### 2. 依存関係のインストール

```powershell
# uv を未インストールの場合: https://docs.astral.sh/uv/getting-started/installation/
uv sync
```

開発・テスト用ツールも入れる場合:

```powershell
uv sync --extra dev
```

### 3. PyTorch（GPU 版）のセットアップ

`uv sync` で入る PyTorch は CPU ビルドです。**GPU 推論（v0.4.0 以降）を使う前に**、環境に合った PyTorch を別途インストールしてください。

| GPU | 参考 |
|-----|------|
| **AMD Radeon (ROCm)** | [PyTorch ROCm 公式手順](https://pytorch.org/get-started/locally/) または [ACE-Step ROCm 起動ガイド](https://github.com/ace-step/ACE-Step-1.5) |
| **NVIDIA (CUDA)** | [PyTorch CUDA 公式手順](https://pytorch.org/get-started/locally/) |
| **GPU なし** | CPU フォールバックで UI とプレースホルダー生成は動作します |

> WSL2 上の ROCm サポートは限定的です。**Radeon ユーザーは Windows ネイティブ環境を推奨**します。

---

## 使い方

### 起動

```powershell
uv run localmusictune
```

ブラウザで **http://127.0.0.1:7860** を開きます。ヘッダー右に検出された GPU（例: `AMD Radeon (ROCm)`）が表示されます。

### モデルのダウンロード

1. 左サイドバー **「モデルの管理」** を開く
2. **「ダウンロードするモデル」** で `ACE-Step 1.5 標準 (2B)` を選択（初回はこれを推奨）
3. **「⬇ 選択モデルをダウンロード」** をクリック
4. 進捗バーが 100% になると **「使用するモデル」** ドロップダウンに `✓保管済み` と表示されます

初回 DL にはネットワーク速度に応じて **数十分〜1 時間程度** かかる場合があります。

### 曲の生成（UI 操作）

1. **イメージ（プロンプト）** に希望の雰囲気を日本語または英語で入力
2. **プリセット** でムードを選択（BPM・楽器・長さのデフォルトが連動）
3. **楽器**・**BPM**・**曲の長さ**・**生成ステップ数** を調整
4. **合成プロンプト（プレビュー）** で最終プロンプトを確認
5. **「🎶 音楽を生成」** をクリック

> v0.3.0 ではプレースホルダー音声が返ります。本番の ACE-Step 推論は次バージョンで有効化されます。

### 生成ファイルの保存先

| 種類 | デフォルトパス |
|------|----------------|
| ダウンロード済みモデル | `./models/` |
| 生成音声 | `./outputs/` |

---

## 設定

`.env.example` を `.env` にコピーしてカスタマイズできます。

| 変数 | 説明 | デフォルト |
|------|------|------------|
| `LMT_MODELS_DIR` | モデル保存先 | `./models` |
| `LMT_OUTPUTS_DIR` | 出力音声保存先 | `./outputs` |
| `LMT_PORT` | Gradio ポート | `7860` |
| `HF_TOKEN` | Hugging Face トークン（ゲートモデル用・任意） | 未設定 |

---

## 対応モデル

[Hugging Face ACE-Step モデル zoo](https://github.com/ace-step/ACE-Step-1.5#-model-zoo) に基づく定義です。

| 名称 | Hugging Face | 用途 |
|------|--------------|------|
| ACE-Step 1.5 標準 (2B) | [`ACE-Step/acestep-v15-base`](https://huggingface.co/ACE-Step/acestep-v15-base) | 軽量・初回推奨 |
| ACE-Step 1.5 XL (4B) | [`ACE-Step/acestep-v15-xl-base`](https://huggingface.co/ACE-Step/acestep-v15-xl-base) | 高品質 |
| ACE-Step 1.5 XL Turbo | [`ACE-Step/acestep-v15-xl-turbo`](https://huggingface.co/ACE-Step/acestep-v15-xl-turbo) | XL 高速版（任意） |

---

## プロジェクト構成

```
LocalMusicTune/
├── app/
│   ├── main.py              # エントリポイント
│   ├── ui.py                # Gradio UI
│   ├── config.py            # パス・定数
│   ├── core/                # GPU 検出・プロンプト合成・音声 I/O
│   ├── models/              # レジストリ・DL 管理・推論バックエンド
│   └── presets/             # ムードプリセット定義
├── assets/mockup.html       # UI 設計モック
├── models/                  # DL モデル（git 管理外）
├── outputs/                 # 生成音声（git 管理外）
├── tests/                   # pytest
├── PLAN.md                  # 開発者向け設計書
└── CHANGELOG.md             # 変更履歴
```

---

## 開発

### テスト

```powershell
uv run pytest
```

### ロードマップ

| バージョン | 内容 | 状態 |
|------------|------|------|
| **v0.3.0** | UI・GPU 検出・プロンプト合成・モデル DL | ✅ リリース済 |
| v0.4.0 | ACE-Step 推論バックエンド（本番生成） | 開発予定 |
| v0.5.0 | 起動スクリプト（AMD / NVIDIA ワンクリック） | 開発予定 |
| v1.0.0 | 配布準備・ドキュメント完成 | 開発予定 |

設計の詳細は [PLAN.md](./PLAN.md) を参照してください。

---

## トラブルシューティング

| 症状 | 対処 |
|------|------|
| ヘッダーが `CPU（GPU未検出）` | GPU 版 PyTorch が入っているか確認。再起動後に再試行 |
| モデル DL が失敗する | ネットワーク・ディスク容量を確認。`HF_TOKEN` が必要な場合は `.env` に設定 |
| `uv sync` が失敗する | Python 3.10+ と uv の最新版を確認 |
| ポート 7860 が使用中 | `.env` で `LMT_PORT=7861` 等に変更 |

---

## ライセンスとクレジット

- **LocalMusicTune** — [MIT License](./LICENSE)
- **推論エンジン [ACE-Step 1.5](https://github.com/ace-step/ACE-Step-1.5)** — MIT License（商用利用可）
- **UI** — [Gradio](https://gradio.app/)（Apache 2.0）

ACE-Step の利用時は、[公式リポジトリ](https://github.com/ace-step/ACE-Step-1.5) および各モデルの Hugging Face ページに記載のライセンス・引用情報に従ってください。

---

## リンク

- リポジトリ: https://github.com/matrix9neonebuchadnezzar2199-sketch/LocalMusicTune
- リリース / タグ: https://github.com/matrix9neonebuchadnezzar2199-sketch/LocalMusicTune/releases
- ACE-Step 1.5: https://github.com/ace-step/ACE-Step-1.5
