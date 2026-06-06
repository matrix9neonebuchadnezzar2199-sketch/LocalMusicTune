# LocalMusicTune

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Status](https://img.shields.io/badge/Status-Pre--release-orange.svg)](https://github.com/matrix9neonebuchadnezzar2199-sketch/LocalMusicTune/releases)
[![ACE-Step](https://img.shields.io/badge/Engine-ACE--Step%201.5-green.svg)](https://github.com/ace-step/ACE-Step-1.5)

**Windows / Linux 向けのローカル AI 音楽生成ツール。** ブラウザ上の Gradio UI から、プロンプト・ムードプリセット・楽器・BPM を指定して曲を生成します。クラウド API 不要、モデルは Hugging Face からローカルに取得して動作します。

> **現在 v0.4.0（プレリリース）** — ACE-Step 1.5 系（標準 2B / XL 4B / XL Turbo）の**本番推論**に対応。DiffRhythm / HeartMuLa / YuE は registry 掲載のみ（推論は今後）。

---

## 特徴

- **完全ローカル** — 生成処理を自分の PC 上で実行（Docker 不要）
- **AMD / NVIDIA 両対応設計** — ROCm（Radeon）を第一級ターゲットに、CUDA も同等にサポート予定
- **直感的な Web UI** — ダークテーマの Gradio インターフェース（[UI モック](./assets/mockup.html) 準拠）
- **7 種類のムードプリセット** — 睡眠・チル・集中・カフェ・ワークアウト・ゲーム・シネマティック
- **ACE-Step 1.5 推論（PHASE 4）** — 公式 `acestep.inference` API をラップ、進捗バー連動・VRAM 警告・CPU フォールバック
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
| XL (4B) | 約 9 GB | 12 GB（オフロード時） | **20 GB**（オフロードなし推奨） |
| XL Turbo | 約 9 GB | 12 GB | 16 GB |

**既定モデルは XL (4B base)** です（開発環境: AMD Radeon RX 7900 XT / 20 GB を想定）。VRAM が厳しい環境では **標準 (2B)** または **XL Turbo** を選んでください。UI は GPU VRAM とモデル要件を比較し、不足時に警告を表示します。

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

開発・テスト用:

```powershell
uv sync --extra dev
uv run pytest
```

GPU なしの CI / ローカル開発のみ CPU 版 torch が必要な場合（**ROCm / CUDA 環境では `--extra cpu` を付けない** — PyPI CPU 版で上書きされます）:

```powershell
uv sync --extra dev --extra cpu
```

### 3. PyTorch（環境別 — `uv sync` では入りません）

**重要:** `torch` / `torchaudio` は `pyproject.toml` の必須依存に**含めていません**。ここに書くと `uv run`（自動 sync）のたびに PyPI の CPU 版が入り、手動で入れた **ROCm / CUDA 版が上書き**されます。

| 環境 | 手順 |
|------|------|
| **AMD Radeon (ROCm)** | 下記 ROCm wheel を `uv pip install`（[ACE-Step ROCm ガイド](https://github.com/ace-step/ACE-Step-1.5) 参照） |
| **NVIDIA (CUDA)** | [PyTorch CUDA 公式](https://pytorch.org/get-started/locally/) の wheel を `uv pip install` |
| **GPU なし（CPU のみ）** | `uv sync --extra cpu` で CPU 版 torch を導入 |

推奨フロー（Radeon / RX 7900 XT 例）:

```powershell
uv sync
# ↓ ROCm 版 PyTorch + ROCm SDK（例: ROCm 7.2 / Python 3.12 / Windows）
# torch wheel 単体では rocm[libraries] 依存で失敗するため、SDK 一式を同時に入れる
uv pip install --no-cache-dir `
  https://repo.radeon.com/rocm/windows/rocm-rel-7.2/rocm-7.2.0.dev0.tar.gz `
  https://repo.radeon.com/rocm/windows/rocm-rel-7.2/rocm_sdk_core-7.2.0.dev0-py3-none-win_amd64.whl `
  https://repo.radeon.com/rocm/windows/rocm-rel-7.2/rocm_sdk_devel-7.2.0.dev0-py3-none-win_amd64.whl `
  https://repo.radeon.com/rocm/windows/rocm-rel-7.2/rocm_sdk_libraries_custom-7.2.0.dev0-py3-none-win_amd64.whl `
  https://repo.radeon.com/rocm/windows/rocm-rel-7.2/torch-2.9.1+rocmsdk20260116-cp312-cp312-win_amd64.whl `
  https://repo.radeon.com/rocm/windows/rocm-rel-7.2/torchaudio-2.9.1+rocmsdk20260116-cp312-cp312-win_amd64.whl `
  https://repo.radeon.com/rocm/windows/rocm-rel-7.2/torchvision-0.24.1+rocmsdk20260116-cp312-cp312-win_amd64.whl

# --no-sync なしで GPU 認識が維持されるか確認
uv run lmt-phase4 gpu-diag
```

> `uv sync` 実行時、手動導入した torch は「定義外」として削除される場合があります。その都度上記 wheel を入れ直してください（PHASE 5 の `start_rocm.bat` で自動化予定）。

> WSL2 上の ROCm サポートは限定的です。**Radeon ユーザーは Windows ネイティブ環境を推奨**します。

### 4. ACE-Step 1.5 推論エンジン（PHASE 4 必須）

本番生成には [ACE-Step 1.5](https://github.com/ace-step/ACE-Step-1.5) パッケージが別途必要です（Python 3.11–3.12 推奨）。ROCm / CUDA 向け PyTorch を先に入れたうえで:

```powershell
# 例: ACE-Step を clone して同一 venv に editable install
git clone https://github.com/ace-step/ACE-Step-1.5.git
cd ACE-Step-1.5
uv sync
uv pip install -e .
```

LocalMusicTune 側では `models/` に DL した重みを `checkpoints/acestep-v15-*` へ自動リンクします。

---

## 使い方

### 起動

```powershell
uv run localmusictune
```

ブラウザで **http://127.0.0.1:7860** を開きます。ヘッダー右に検出された GPU（例: `AMD Radeon (ROCm)`）が表示されます。

### モデルのダウンロード

1. 左サイドバー **「モデルの管理」** を開く
2. **「ダウンロードするモデル」** で `ACE-Step 1.5 XL (4B / 高品質)` を選択（**既定** — 20 GB VRAM 向け）
3. **「⬇ 選択モデルをダウンロード」** をクリック
4. 進捗バーが 100% になると **「使用するモデル」** ドロップダウンに `✓保管済み` と表示されます

> 手軽に試す・DL を短時間で済ませたい場合は **標準 (2B)**（約 4.7 GB）も選べます。

初回 DL にはネットワーク速度に応じて **数十分〜1 時間程度** かかる場合があります。

### 曲の生成（UI 操作）

1. **イメージ（プロンプト）** に希望の雰囲気を日本語または英語で入力
2. **プリセット** でムードを選択（BPM・楽器・長さのデフォルトが連動）
3. **楽器**・**BPM**・**曲の長さ**・**生成ステップ数** を調整
4. **合成プロンプト（プレビュー）** で最終プロンプトを確認
5. **「🎶 音楽を生成」** をクリック
6. **生成の進捗** にステップ `n/N` とスライダーが表示されます（初回は数分〜かかる場合があります）
7. 完了後、**生成された曲** プレイヤーで WAV を再生

> **ace-step 未インストール時**はエラーになります。[ACE-Step セットアップ](#4-acestep-15-推論エンジンphase-4-必須) を先に完了してください。

### PHASE 4 検証 CLI（Radeon 実機推奨）

```powershell
uv run lmt-phase4 gpu-diag
uv run lmt-phase4 ace-load --model ace-1.5-standard
uv run lmt-phase4 ace-generate --model ace-1.5-standard --duration 10 --steps 20 -v
```

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

**配布方針:** 商用利用可能なモデル（MIT / Apache-2.0）のみ UI に掲載しています。役割が異なるモデルを「数を増やす」のではなく**住み分け**で選べます。

### 商用可モデル（ダウンロード・選択可能）

| モデル | ライセンス | 向いている用途 | 最長 | VRAM 目安 | 推論 |
|--------|-----------|----------------|------|-----------|------|
| **ACE-Step 1.5 XL (4B)** | MIT | **既定。** 高品質万能（歌・インスト） | 4分 | 12〜20 GB | PHASE 4 |
| ACE-Step 1.5 標準 (2B) | MIT | 軽量・高速試行 | 4分 | 4〜8 GB | PHASE 4 |
| ACE-Step 1.5 XL Turbo | MIT | 8ステップ高速・試行錯誤 | 4分 | 12〜16 GB | PHASE 4 |
| [DiffRhythm](https://github.com/ASLP-lab/DiffRhythm) full | Apache-2.0 | 歌+伴奏フルソングを**超高速**生成 | **4分45秒** | 8 GB〜 | 近日対応 |
| [HeartMuLa](https://github.com/HeartMuLa/HeartLib) 3B | Apache-2.0 | 歌モノ・話題の新顔 | 6分 | 8〜16 GB | 近日対応 |
| [YuE](https://huggingface.co/m-a-p/YuE-s1-7B-anneal-en-icl) 7B | Apache-2.0 | 歌詞重視・長尺（**生成は遅め**） | 5分 | 10〜16 GB | 近日対応 |

> **RX 7900 XT（20 GB）** では上記すべて快適に動作する想定です。曲の長さスライダーは選択モデルの上限に自動連動します。

推論バックエンド未実装のモデルは「**近日対応**」と表示され、DL と UI 確認まで可能です。実装順序: **ACE-Step 系 → DiffRhythm → YuE → HeartMuLa**（[PLAN.md](./PLAN.md) §7）。

### 非商用モデル（参考のみ — UI 非掲載）

| モデル | ライセンス | 理由 |
|--------|-----------|------|
| MusicGen (Meta) | CC BY-NC | 非商用。1回約30秒の短尺BGM向け |
| Stable Audio Open | Stability AI Community License | 一定規模以上の商用に制限 |

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
| **v0.3.1** | XL 既定化・VRAM 警告 | ✅ リリース済 |
| **v0.3.2** | 多モデル registry 拡充 | ✅ リリース済 |
| **v0.4.3** | Gradio 6 UI + 生成ボタン接続 + 進捗バー実連動 | ✅ リリース済 |
| **v0.4.2** | ROCm パッチ + XL 初回音出し | ✅ リリース済 |
| v0.5.0 | 起動スクリプト（AMD / NVIDIA ワンクリック） | 開発予定 |
| v1.0.0 | 配布準備・ドキュメント完成 | 開発予定 |

設計の詳細は [PLAN.md](./PLAN.md) を参照してください。

---

## トラブルシューティング

| 症状 | 対処 |
|------|------|
| `ImportError: cannot import name 'group' from 'torch.distributed'` | v0.4.2+ では起動時に自動パッチ。手動なら `vector_quantize_pytorch/lookup_free_quantization.py` の distributed import を try/except 化 |
| `uv run` 後に GPU 未検出 / CPU 版 torch に戻る | `pyproject.toml` の `dependencies` に torch が無いか確認。ROCm wheel を `uv pip install` し直す |
| ヘッダーが `CPU（GPU未検出）` | GPU 版 PyTorch が入っているか確認。`uv run lmt-phase4 gpu-diag` |
| モデル DL が失敗する | ネットワーク・ディスク容量を確認。`HF_TOKEN` が必要な場合は `.env` に設定 |
| `uv sync` が失敗する | Python 3.10+ と uv の最新版を確認 |
| 生成ボタンが「ace-step 未インストール」 | README § ACE-Step セットアップを実施 |
| `lmt-phase4 gpu-diag` が FAIL | GPU 版 PyTorch / ROCm ドライバを確認。Windows ネイティブ ROCm 推奨 |

---

## ライセンスとクレジット

- **LocalMusicTune** — [MIT License](./LICENSE)
- **推論エンジン** — [ACE-Step 1.5](https://github.com/ace-step/ACE-Step-1.5)（MIT）、[DiffRhythm](https://github.com/ASLP-lab/DiffRhythm)（Apache-2.0）、[HeartMuLa](https://github.com/HeartMuLa/HeartLib)（Apache-2.0）、[YuE](https://huggingface.co/m-a-p/YuE-s1-7B-anneal-en-icl)（Apache-2.0）
- **UI** — [Gradio](https://gradio.app/)（Apache 2.0）

ACE-Step の利用時は、[公式リポジトリ](https://github.com/ace-step/ACE-Step-1.5) および各モデルの Hugging Face ページに記載のライセンス・引用情報に従ってください。

---

## リンク

- リポジトリ: https://github.com/matrix9neonebuchadnezzar2199-sketch/LocalMusicTune
- リリース / タグ: https://github.com/matrix9neonebuchadnezzar2199-sketch/LocalMusicTune/releases
- ACE-Step 1.5: https://github.com/ace-step/ACE-Step-1.5
