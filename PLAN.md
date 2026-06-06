# PLAN.md — ローカル音楽生成ツール「LocalMusicTune」 全体設計

## 1. プロジェクト概要

Windows 11 上で、WSL2（Ubuntu）またはWindowsネイティブのPython環境で動作する、ローカル音楽生成ツール。Gradioによる自作WebUIを通じて、プロンプト・プリセット・楽器・BPM・長さを指定して音楽を生成する。AMD（ROCm）/ NVIDIA（CUDA）の両GPUに、起動スクリプトの出し分けで対応する。Dockerは使用しない。

開発者の実環境はAMD Radeon RX 7900 XT（20 GB VRAM）。よって**AMD/ROCm版を第一級の動作対象**とし、NVIDIA/CUDA版も同等に対応する。生成エンジンの土台はACE-Step 1.5（MITライセンス、商用可）を採用する。**既定モデルは XL（4B base）** — 20 GB VRAM でオフロードなし運用を想定（詳細は §7）。

## 2. 技術スタック

バックエンド・UIともにPython + Gradioで統一する。理由は、UIとモデル推論を同一プロセスで扱え、進捗コールバックやファイル受け渡しが容易なため。具体的には、UIフレームワークにGradio、推論にPyTorch（ROCmビルド / CUDAビルドを環境で出し分け）、モデル取得に huggingface_hub、音声処理に soundfile / torchaudio を用いる。環境管理は uv を採用し、Dockerは使わない。

## 3. フォルダ構成

```
LocalMusicTune/
├── PLAN.md                  # 本ドキュメント
├── README.md                # 利用者向け導入手順（NVIDIA/AMD別の導線）
├── LICENSE                  # MIT
├── pyproject.toml           # uv / 依存定義
├── .gitignore               # models/ や outputs/ を除外
├── .env.example             # 設定例（モデル保存先など）
│
├── run.sh                   # Linux/WSL2 共通エントリ（GPU自動判定）
├── start_nvidia.sh          # CUDA版で起動
├── start_rocm.sh            # ROCm版で起動
├── run.bat                  # Windowsネイティブ用エントリ
├── start_rocm.bat           # Windowsネイティブ ROCm起動
│
├── app/
│   ├── __init__.py
│   ├── main.py              # エントリポイント。Gradio起動
│   ├── ui.py                # Gradio UI定義（モックHTMLを移植）
│   ├── config.py            # 設定・パス・定数の集中管理
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── device.py        # GPU検出（CUDA/ROCm/CPU）と判定
│   │   ├── generator.py     # 音楽生成の中核（モデル呼び出し・進捗）
│   │   ├── prompt_builder.py# プロンプト合成（楽器/BPM/プリセット→文）
│   │   └── audio.py         # 出力音声の保存・後処理
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── registry.py      # 利用可能モデルの定義（名前/容量/VRAM/repo）
│   │   ├── manager.py       # DL・保管済みスキャン・削除・進捗
│   │   └── backends/
│   │       ├── __init__.py
│   │       ├── base.py      # 推論バックエンドの抽象インターフェース
│   │       └── ace_step.py  # ACE-Step 1.5 実装
│   │
│   └── presets/
│       ├── __init__.py
│       └── presets.py       # プリセット定義（睡眠/チル等→prompt+params）
│
├── assets/
│   └── mockup.html          # 確認済みUIモック（設計の参照用）
│
├── models/                  # DLしたモデルの保管先（git管理外）
├── outputs/                 # 生成した音声の出力先（git管理外）
└── tests/
    ├── test_prompt_builder.py
    ├── test_registry.py
    └── test_device.py
```

設計の要点は分離にある。GPU判定（device.py）、プロンプト組み立て（prompt_builder.py）、モデル管理（manager.py）、推論バックエンド（backends/）をそれぞれ独立させ、UI（ui.py）はこれらを呼ぶだけにする。こうしておくと、将来ACE-Step以外のモデル（DiffRhythm等）を足すときは backends/ に1ファイル追加するだけで済み、AMD/NVIDIAの差分は device.py と起動スクリプトに閉じ込められる。

## 4. 開発フェーズ（PHASE）

各フェーズは「Cursorに実装させる単位」であり、末尾の検証は**開発者が実機で行う**。前フェーズの検証が通るまで次に進まない。

**PHASE 0 — 土台とスキャフォールド**
リポジトリ初期化、フォルダ構成・空ファイル作成、pyproject.toml、.gitignore、README骨子を用意する。config.py にパス定数（models/、outputs/）を定義。この段階ではまだ推論はしない。検証は、`uv sync` が通り、フォルダ構成が揃っていること。

**PHASE 1 — GPU検出とダミーUI起動**
device.py でCUDA/ROCm/CPUを判定するロジックを実装し、ui.py に確認済みモックHTMLのレイアウトをGradioで再現する（プロンプト欄、プリセット、楽器チェック、スライダー、モデル選択、進捗バー、ヘッダー右のGPU表示）。この時点では生成ボタンはダミー（無音ファイルか固定音を返す）。検証は、ブラウザでUIが表示され、ヘッダーに「AMD Radeon (ROCm)」等が正しく出ること。**ここが最初の山場なので、Radeon実機での表示確認を必ず行う。**

**PHASE 2 — プロンプト合成とプリセット**
prompt_builder.py と presets.py を実装。楽器チェックボックス・BPMスライダー・プリセット選択を、最終的にモデルへ渡す1つのプロンプト文＋パラメータに合成する。プリセット（睡眠/チル/集中/カフェ/ワークアウト/ゲーム/シネマティック）を定義。検証は、UIで設定を変えると生成プロンプトのプレビュー文字列が期待どおり変わること（UIにデバッグ表示を一時的に出すとよい）。tests/test_prompt_builder.py を用意。

**PHASE 3 — モデル管理（ダウンロードと保管済み判定）**
registry.py に対応モデルの定義（ACE-Step 1.5 / XL など、repo・推定容量・必要VRAM）を書き、manager.py で huggingface_hub によるDL、保管済みスキャン、DL進捗の取得を実装する。UIのサイドバー（保管済みのみ選択可、未DLはダウンロードボタン、DL中は進捗バー）と接続。検証は、実際に1つモデルをDLでき、進捗バーが動き、DL後はドロップダウンに「保管済み」として現れること。

**PHASE 4 — ACE-Step推論バックエンド（本命）**
backends/base.py の抽象を定義し、ace_step.py でACE-Step 1.5の実際の推論を実装。generator.py が、選択モデル・合成プロンプト・パラメータを受けて音声を生成し、生成ステップの進捗をUIの進捗バーへコールバックする。出力は audio.py で outputs/ に保存。**Radeon/ROCmで実際に音が鳴ることをここで確認する。** VRAM不足時のオフロード/量子化の扱いもこのフェーズで詰める。検証は、Radeon実機でプロンプトから曲が生成・再生でき、進捗バーが実進捗に連動すること。

**PHASE 5 — 起動スクリプトと両対応の仕上げ**
run.sh / start_nvidia.sh / start_rocm.sh / run.bat / start_rocm.bat を整備。GPUを自動判定して適切なPyTorch（ROCm版/CUDA版）と起動経路を選ぶ。Windowsネイティブ ROCm 経路（ACE-Step公式の rocm 起動方式に倣う）も用意。検証は、Radeon環境でワンクリック起動できること。NVIDIA環境は手元になければREADMEに手順を記し、可能なら別途検証。

**PHASE 6 — 仕上げ・配布準備**
README完成（NVIDIA/AMD別の前提条件と導入手順、トラブルシューティング）、エラーハンドリング、出力履歴の整理、ライセンス確認（ACE-Stepおよび依存物のライセンス表記）。検証は、クリーンな環境でREADMEだけを見て導入できること。

## 5. Cursorへの作業ルール（重要）

Cursorに渡す際、次の原則を守らせる。フェーズは順番に1つずつ実装し、勝手に先のフェーズへ進まない。各フェーズ完了時に「何を検証すべきか」を開発者に提示してから次へ進む。GPU/ROCm依存のコードは、CPUフォールバックを必ず用意し、GPUがなくても最低限UIと生成（低速）が動くようにする。秘密情報やモデル本体はコミットしない（.gitignoreで models/ outputs/ を除外）。外部仕様（ACE-Stepの正確なAPIや起動方法）は推測で書かず、不明点は実装前に公式リポジトリのREADME/INSTALLを確認する。

## 6. 既知のリスクと対処

最大のリスクはAMD ROCmのWSL2サポートが限定的な点。対処として、開発者（Radeon RX 7900 XT）は**WindowsネイティブのROCm起動経路**（`start_rocm.bat`）を主軸とし、WSL2版は後回しか任意とする。RDNA3（7900 XT/XTX）はROCm対応が進んでいるが、ROCmバージョンや起動経路によってつまずきが変わるため、PHASE 4・5 の実機検証は Windows ネイティブから始める。

次のリスクはBPMや楽器がモデルの直接パラメータでなくプロンプト誘導である点。これは「確実な保証ではなく傾向制御」と割り切り、プリセット側のプロンプト文で品質を担保する。

VRAM不足は、registry.py の `vram_min_gb` と実GPUのVRAMを比較し、UIで警告を出す（足りない場合: 「標準2BかXL Turboをお試しください」）。配布先ユーザー向けの安全策として常に残す。

---

## 7. モデル選定（確定方針）

### 用語整理

| 呼称 | 実体 | 重み目安 | VRAM |
|------|------|----------|------|
| **標準** | 2B クラス（`acestep-v15-base`） | 約 4.7 GB | 4 GB〜（推奨 8 GB） |
| **XL** | 4B クラス（`acestep-v15-xl-*`） | 約 9 GB | 12 GB〜（オフロード時）/ 20 GB 推奨（オフロードなし） |

「標準＝4B」ではなく **「標準＝2B」「XL＝4B」** である。

### 開発環境（RX 7900 XT / 20 GB VRAM）

開発者の実GPUは **AMD Radeon RX 7900 XT（20 GB）**。XL（4B base）のオフロードなし推奨ライン（20 GB）に一致するため、**registry の `default` は XL（4B base）** とする。

| モデル | 役割 | `default` |
|--------|------|-----------|
| XL (4B base) | 高品質・既定モデル | **True** |
| 標準 (2B) | 軽量・高速試行用 | False |
| XL Turbo | 8ステップ高速版・試行錯誤用オプション | False（optional） |

RX 7900 XT では3モデルすべての VRAM 要件を満たすため、開発者環境では警告は通常出ない。他ユーザー（VRAM 不足）向けに警告ロジックは維持する。

### registry 参照

実装は `app/models/registry.py`。**商用可（MIT / Apache-2.0）のみ** UI に掲載。MusicGen（CC BY-NC）や Stable Audio Open（Community License）は `NON_COMMERCIAL_MODELS` に文書化のみ。

### モデル役割分担（確定）

| キー | 家族 | 役割 | 最長 | 推論 |
|------|------|------|------|------|
| ace-1.5-xl-base | ACE-Step | **既定・高品質万能** | 240秒 | PHASE 4 最優先 |
| ace-1.5-standard | ACE-Step | 軽量・高速試行 | 240秒 | PHASE 4 |
| ace-1.5-xl-turbo | ACE-Step | 高速試行錯誤 | 240秒 | PHASE 4 |
| diffrhythm-full | DiffRhythm | 超高速フルソング | **285秒** | PHASE 4 後 |
| heartmula-3b | HeartMuLa | 歌モノ・話題モデル | 360秒 | PHASE 4 後（API 流動性に注意） |
| yue-7b | YuE | 歌詞重視・長尺・低速 | 300秒 | PHASE 4 後 |

未対応バックエンドは UI で「近日対応」表示。曲長スライダー上限は `max_duration_sec` に連動。

### PHASE 3・4 の検証方針

- **PHASE 3**: 全商用モデルの DL・保管済み表示。DL 検証の最低ラインは標準 (2B)（容量小）。既定 DL ターゲットは XL。
- **PHASE 4**: ACE-Step 系 3 モデルを先に完成 → DiffRhythm → YuE → HeartMuLa の順で `backends/` を追加。開発環境（RX 7900 XT / 20 GB）では **XL を主軸**に ROCm 実機検証。
