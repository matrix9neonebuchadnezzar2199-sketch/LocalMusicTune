# PLAN.md — ローカル音楽生成ツール「LocalMusicTune」 全体設計

## 1. プロジェクト概要

Windows 11 上で、WSL2（Ubuntu）またはWindowsネイティブのPython環境で動作する、ローカル音楽生成ツール。Gradioによる自作WebUIを通じて、プロンプト・プリセット・楽器・BPM・長さを指定して音楽を生成する。AMD（ROCm）/ NVIDIA（CUDA）の両GPUに、起動スクリプトの出し分けで対応する。Dockerは使用しない。

開発者の実環境はAMD Radeon。よって**AMD/ROCm版を第一級の動作対象**とし、NVIDIA/CUDA版も同等に対応する。生成エンジンの土台はACE-Step 1.5（MITライセンス、商用可）を採用する。

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

最大のリスクはAMD ROCmのWSL2サポートが限定的な点。対処として、開発者（Radeon）はまずWindowsネイティブのROCm起動経路を主軸にし、WSL2版は後回しか任意とする。次のリスクはBPMや楽器がモデルの直接パラメータでなくプロンプト誘導である点で、これは「確実な保証ではなく傾向制御」と割り切り、プリセット側のプロンプト文で品質を担保する。VRAM不足は、registry.py に必要VRAMを持たせ、UIで実GPUに対し重すぎるモデルを選んだら警告を出す方針とする。

---

このPlanで、Cursorには「PHASE 0から順に実装して」と指示すれば段階的に進められます。各フェーズ末の検証ポイントをあなたが実機で確認しながら進めれば、ROCm特有のつまずきも早期に見つけられます。

正確な情報が取れました。一点だけ、あなたが言う「標準（4B）」について重要な認識合わせが必要です。

調べた結果、ACE-Step 1.5 の用語整理はこうなっています。「標準」と呼ばれているのは実は **2B** クラスのモデル（重み約4.7GB、4GB前後のVRAMでも動く軽量版）で、**4B というのは XL シリーズのほう**（`acestep-v15-xl-*`、重み約9GB、12GB以上のVRAM）なんです。つまり「標準＝4B」ではなく、「標準＝2B」「XL＝4B」という関係でした。

なので、あなたの意図は「軽くて動かしやすい標準版」と「高品質なXL版」の2本立て、という理解で進めるのが自然だと思います。その前提で registry を組みます。

ここでRadeonユーザーであるあなたに関わる現実的なポイントがあります。XL（4B）はオフロード＋INT8量子化でも12GB以上、快適に動かすなら20GB以上が推奨です。お使いのRadeonのVRAMがこれに届くかで、XLが実用になるか変わります。もしVRAMが足りない場合に備えて、XLには **Turbo版**（`acestep-v15-xl-turbo`、わずか8ステップで生成できる蒸留高速版）も選択肢として registry に入れておくと、Radeonでも現実的に使える保険になります。

これを踏まえて registry を確定させると、次のようになります。

```python
# app/models/registry.py
# ACE-Step 1.5 対応モデル定義
# 注意：repo_id・VRAM要件は公式リポジトリ/モデルカードの値に基づく。
#       実装前に最新のrepo_idを必ず再確認すること。

MODELS = {
    "ace-1.5-standard": {
        "display_name": "ACE-Step 1.5 標準 (2B)",
        "repo_id": "ACE-Step/Ace-Step1.5",      # 2Bクラス標準版
        "weights_size_gb": 4.7,                  # 重みの目安
        "vram_min_gb": 4,                        # 4GB前後から動作
        "vram_recommended_gb": 8,
        "note": "軽量で動かしやすい。まず試すならこれ。",
        "default": True,
    },
    "ace-1.5-xl-base": {
        "display_name": "ACE-Step 1.5 XL (4B / 高品質)",
        "repo_id": "ACE-Step/acestep-v15-xl-base",
        "weights_size_gb": 9.0,
        "vram_min_gb": 12,                       # offload+INT8量子化で12GB〜
        "vram_recommended_gb": 20,               # offloadなしは20GB〜推奨
        "note": "高品質。VRAMに余裕がある場合向け。",
        "default": False,
    },
    # Radeon等でVRAMが厳しい場合の保険（任意で有効化）
    "ace-1.5-xl-turbo": {
        "display_name": "ACE-Step 1.5 XL Turbo (高速 / 8ステップ)",
        "repo_id": "ACE-Step/acestep-v15-xl-turbo",
        "weights_size_gb": 9.0,
        "vram_min_gb": 12,
        "vram_recommended_gb": 16,
        "note": "8ステップで高速生成する蒸留版。XLが重い環境向け。",
        "default": False,
    },
}
```
追記：

PHASE 3（モデル管理）は、上記 registry の標準（2B）とXL（4B base）の2モデルを正式対応として実装し、XL Turbo は任意の追加候補として枠だけ用意する、という形にします。検証は、標準（2B）を実際にダウンロードできて保管済み表示になることを最低ラインとします（容量が小さく検証が速いため）。

PHASE 4（推論バックエンド）は、まず軽い標準（2B）でRadeon実機で音が鳴ることを最優先で確認し、それが通ってからXLに進む順序にします。XLはVRAM不足が起きやすいので、UIで実GPUのVRAMと選択モデルの `vram_min_gb` を比較して、足りない場合は警告を出す処理をここに入れます。

PLAN.mdの「6. 既知のリスク」にも、VRAMに関する具体的な数値（標準2Bは4〜8GB、XL 4Bは12GB以上推奨）を追記し、「Radeonでメモリが厳しければ標準2BまたはXL Turboを使う」という方針を明記します。
