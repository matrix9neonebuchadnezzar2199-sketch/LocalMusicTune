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
# リポジトリを clone 後
cd LocalMusicTune
uv sync
uv run localmusictune
```

ブラウザで `http://127.0.0.1:7860` を開きます。

## 開発フェーズ

| PHASE | 内容 | 状態 |
|-------|------|------|
| 0 | 土台・スキャフォールド | ✅ 完了 |
| 1 | GPU 検出・ダミー UI | 未着手 |
| 2 | プロンプト合成・プリセット | 未着手 |
| 3 | モデル管理（DL） | 未着手 |
| 4 | ACE-Step 推論 | 未着手 |
| 5 | 起動スクリプト | 未着手 |
| 6 | 配布準備 | 未着手 |

詳細は [PLAN.md](./PLAN.md) を参照。

## ライセンス

本プロジェクトは MIT ライセンスです。ACE-Step および各依存ライブラリのライセンスは PHASE 6 で整理予定。
