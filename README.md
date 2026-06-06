# LocalMusicTune

Windows 11 上で動作するローカル音楽生成ツール。Gradio Web UI からプロンプト・プリセット・楽器・BPM を指定して音楽を生成します。推論エンジンは [ACE-Step 1.5](https://github.com/ace-step/ACE-Step)（MIT）を採用予定です。

## 対応 GPU

| 環境 | 起動方法 | 状態 |
|------|----------|------|
| AMD Radeon (ROCm) | `start_rocm.bat` / `start_rocm.sh` | 開発中（第一級対象） |
| NVIDIA (CUDA) | `start_nvidia.sh` | 開発中 |
| CPU フォールバック | `run.bat` / `run.sh` | 開発中 |

## 前提条件

- Python 3.10+
- [uv](https://docs.astral.sh/uv/)（推奨パッケージマネージャ）
- AMD: ROCm 対応 PyTorch（Windows ネイティブ推奨）
- NVIDIA: CUDA 対応 PyTorch

## クイックスタート（開発中）

```powershell
cd LocalMusicTune
uv sync
uv run localmusictune
```

ブラウザで `http://127.0.0.1:7860` を開きます。ヘッダー右に検出 GPU（例: AMD Radeon ROCm）が表示され、生成ボタンはダミー音声（440Hz 短音）を返します。

### 検証（PHASE 1）

- [ ] ブラウザで UI が mockup に近いレイアウトで表示される
- [ ] ヘッダーに GPU 名・起動モードが正しく出る（Radeon 実機推奨）
- [ ] 生成ボタンで進捗バーが動き、音声が再生できる

### 検証（PHASE 2）

- [ ] プリセット・楽器・BPM を変えると「合成プロンプト（プレビュー）」が期待どおり更新される
- [ ] プリセット変更で BPM / 楽器 / 長さ / ステップのデフォルトが切り替わる
- [ ] `uv run pytest tests/test_prompt_builder.py` が通る

## 開発フェーズ

| PHASE | 内容 | 状態 |
|-------|------|------|
| 0 | 土台・スキャフォールド | ✅ 完了 |
| 1 | GPU 検出・ダミー UI | ✅ 完了 |
| 2 | プロンプト合成・プリセット | ✅ 完了 |
| 3 | モデル管理（DL） | 未着手 |
| 4 | ACE-Step 推論 | 未着手 |
| 5 | 起動スクリプト | 未着手 |
| 6 | 配布準備 | 未着手 |

詳細は [PLAN.md](./PLAN.md) を参照。

## ライセンス

本プロジェクトは MIT ライセンスです。ACE-Step および各依存ライブラリのライセンスは PHASE 6 で整理予定。
