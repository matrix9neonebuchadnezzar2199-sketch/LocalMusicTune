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
│   ├── mockup.html          # 1画面 UI モック（現行 Gradio の参照）
│   └── mockup-steps.html    # ステップ UI + モーション検証（Smart Animate 相当）
├── docs/
│   └── UI_DESIGN.md         # UI 設計・モーション仕様（§3 トークン）
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
run.sh / start_nvidia.sh / start_rocm.sh / run.bat / start_rocm.bat を整備。GPUを自動判定して適切なPyTorch（ROCm版/CUDA版）と起動経路を選ぶ。Windowsネイティブ ROCm 経路（ACE-Step公式の rocm 起動方式に倣う）も用意。

**PyTorch 依存の扱い（PHASE 5 で明文化・起動スクリプトで担保）**
- `pyproject.toml` の `dependencies` に **torch / torchaudio を含めない**（`+cpu` / `+rocm` / `+cu*` は環境ごとに別物のため）。
- CPU フォールバックのみ `[project.optional-dependencies] cpu` extra に記載。
- `start_rocm.bat` 等は起動前に ROCm 版 torch の有無を確認し、未導入なら wheel 導入を案内または実行する。
- `uv run`（自動 sync）で CPU 版に巻き戻らないことを README トラブルシューティングにも記載。

検証は、Radeon環境でワンクリック起動できること。NVIDIA環境は手元になければREADMEに手順を記し、可能なら別途検証。

**PHASE 6 — 仕上げ・配布準備**
README完成（NVIDIA/AMD別の前提条件と導入手順、トラブルシューティング）、エラーハンドリング、出力履歴の整理、ライセンス確認（ACE-Stepおよび依存物のライセンス表記）。検証は、クリーンな環境でREADMEだけを見て導入できること。

## 5. Cursorへの作業ルール（重要）

Cursorに渡す際、次の原則を守らせる。フェーズは順番に1つずつ実装し、勝手に先のフェーズへ進まない。各フェーズ完了時に「何を検証すべきか」を開発者に提示してから次へ進む。GPU/ROCm依存のコードは、CPUフォールバックを必ず用意し、GPUがなくても最低限UIと生成（低速）が動くようにする。秘密情報やモデル本体はコミットしない（.gitignoreで models/ outputs/ を除外）。外部仕様（ACE-Stepの正確なAPIや起動方法）は推測で書かず、不明点は実装前に公式リポジトリのREADME/INSTALLを確認する。

## 6. 既知のリスクと対処

最大のリスクはAMD ROCmのWSL2サポートが限定的な点。対処として、開発者（Radeon RX 7900 XT）は**WindowsネイティブのROCm起動経路**（`start_rocm.bat`）を主軸とし、WSL2版は後回しか任意とする。RDNA3（7900 XT/XTX）はROCm対応が進んでいるが、ROCmバージョンや起動経路によってつまずきが変わるため、PHASE 4・5 の実機検証は Windows ネイティブから始める。

次のリスクはBPMや楽器がモデルの直接パラメータでなくプロンプト誘導である点。これは「確実な保証ではなく傾向制御」と割り切り、プリセット側のプロンプト文で品質を担保する。

VRAM不足は、registry.py の `vram_min_gb` と実GPUのVRAMを比較し、UIで警告を出す（足りない場合: 「標準2BかXL Turboをお試しください」）。配布先ユーザー向けの安全策として常に残す。

**PyTorch / uv の巻き戻り:** `dependencies` に `torch` を書くと `uv run` のたびに PyPI の CPU 版が入り、手動導入した ROCm/CUDA 版が上書きされる。対処は torch を本体依存から外し、GPU 別 wheel は起動スクリプトまたは手動 `uv pip install` で管理する（PHASE 5）。

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

追記：

## PHASE 4 — ACE-Step系 推論バックエンド（サブステップ分解）

このフェーズはプロジェクト最大の関門であり、RX 7900 XT + ROCm環境で「実際に音が鳴る」ことを確認する核心部分である。一気に通そうとせず、下記のサブステップを順番に実施し、各ステップの検証が通るまで次へ進まない。各検証は開発者がRadeon実機で行う。詰まった場合の切り分けを容易にするため、最軽量モデル・最短尺・最小ステップから始める。

**前提・原則**
最初の音出しが通るまで、進捗バーの実連動・VRAM警告・XL対応・複数モデル対応はすべて後回しにする。各サブステップは独立して検証可能な単位とし、CPUフォールバック経路を常に残す(GPUが使えない場合でも低速で動くこと)。エラーが出たら「ROCm/環境の問題」か「モデル/コードの問題」かを必ず切り分けてから次へ進む。

**ROCm Windows 既知パッチ（#404 修正1 — 実装済み `app/core/patches.py`）**
- `vector_quantize_pytorch` が `torch.distributed.group` を無条件 import → ROCm Windows では ImportError。
- 起動時に `lookup_free_quantization.py` へ distributed フォールバックを自動パッチ（`apply_rocm_windows_patches()` を `main.py` / `lmt-phase4` 先頭で実行）。
- 20GB ちょうどで XL をフル GPU ロードすると diffusion 用 VRAM が足りない → `vram_gb <= vram_recommended_gb` で `offload_to_cpu=True`（ACE-Step プリフライトをスキップ）。

**PHASE 4-1 — 環境疎通（音を作らない）**
PyTorchがROCm経由でGPUを認識するかだけを確認する。`device.py` の判定結果を使い、`torch` がGPUを見えているか、簡単なテンソル演算がGPU上で走るかを確かめる小さな診断スクリプト（または起動時ログ）を用意する。まだACE-Stepはロードしない。
検証：RX 7900 XT が ROCm デバイスとして認識され、GPU上で簡単な計算が成功する。ここが通らなければモデル以前の環境問題であり、`start_rocm.bat`（Windowsネイティブ）経路を優先して切り分ける。

**PHASE 4-2 — モデルのロードのみ（推論しない）**
`backends/ace_step.py` で、標準(2B)モデルをメモリ/VRAMにロードするところまで実装する。ロード成功と、おおよそのVRAM使用量をログ出力する。まだ生成はしない。
検証：標準(2B)がエラーなくロードでき、VRAM使用量が想定内（重み約4.7GB前後）に収まる。ロードで落ちる場合は量子化/dtype/ROCm依存の問題をここで特定する。

**PHASE 4-3 — 最小の音出し（2B・固定設定）**
標準(2B)で、最短尺（例：10秒）・最小ステップ数・固定の単純なプロンプト1つを使い、とにかく音声ファイルを1つ生成して `outputs/` に保存する。UI連携や進捗表示はまだ不要で、CLIから関数を直接叩く形でよい。
検証：**Radeon実機で、プロンプトから10秒の音声が生成・保存され、実際に再生して音が鳴る。** これがプロジェクト最大のマイルストーン。ここが通れば技術的な実現性が確定する。

**PHASE 4-4 — UIとの接続（2B）** ✅ 実装済（v0.4.3）
4-3の生成関数を Gradio UI の「生成」ボタン・プロンプト欄・スライダー・`prompt_builder` と接続。Gradio 6 ジェネレータ方式で非ブロッキング。CLI と同一の `MusicGenerator.generate` パス。オフロード自動判定を継承。
検証：UI上でプロンプトと長さを指定して生成ボタンを押すと、曲が生成され、プレイヤーで再生できる。

**PHASE 4-5 — 進捗バーの実連動** ✅ 実装済（v0.4.3）
ACE-Stepの拡散ステップ進行をコールバックで取得し、UIの進捗テキスト（ステップ n/N）とスライダーへ反映。初回遅延の案内を表示。
検証：生成中に進捗バーが実際のステップ進行に連動して動く。

**PHASE 4-6 — XL(4B)対応とモデル切り替え**
registryの選択に応じて、標準(2B)とXL(4B base)をUIから切り替えてロード・生成できるようにする。RX 7900 XT(20GB)ではXLをオフロードなしで動かせる想定だが、ロード/生成のVRAM挙動を実測で確認する。既定をXL(4B)に設定。
検証：UIでモデルを切り替えて、XL(4B)でも生成・再生できる。XLと2Bでメモリと速度の差を確認する。

**PHASE 4-7 — XL Turbo対応**
XL Turbo（8ステップ高速版）をバックエンドに追加し、ステップ数の扱い（Turboは少ステップ前提）を調整する。
検証：Turboで、通常XLより明確に短い時間で生成が完了する。

**PHASE 4-8 — VRAM警告とフォールバック**
実GPUのVRAMと選択モデルの `vram_min_gb` を比較し、不足時はUIに警告を出す。あわせてVRAM不足時のオフロード/量子化の扱い、最終的なCPUフォールバック経路を整える(他者の少VRAM環境での配布を想定)。
検証：（擬似的に）VRAMが少ない条件で重いモデルを選ぶと警告が出る。CPUのみ環境でも(低速ながら)生成が完走する。

**PHASE 4 完了の定義(Definition of Done)**
RX 7900 XT + ROCm 上で、ACE-Step 標準(2B)・XL(4B)・XL Turbo の3モデルすべてが、UIから生成・再生でき、進捗バーが実連動し、VRAM警告とCPUフォールバックが機能している状態。これをもってPHASE 4完了とし、次の拡張フェーズ(DiffRhythm対応)へ進む。

---

分解の意図を補足しておきます。一番のポイントは 4-1〜4-3 を「音を作る前」「ロードだけ」「最小の音出し」と3段階に割ったところです。ROCmで詰まったとき、4-1で落ちれば環境問題、4-2で落ちればロード/dtype/量子化、4-3で落ちれば生成ロジック、と原因の層がはっきり切り分けられます。ここを一気にやると「何が悪いのか分からない」状態に陥りやすいので、あえて細かくしています。また、既定をXLにする設定（4-6）も、最初の音出しを軽い2Bで通してから入れることで、「XLが重いせいで動かない」のか「そもそも動かない」のかを混同せずに済みます。

Cursorに渡すときは、この4-1から1つずつ「4-1を実装して、検証方法を提示してから止まって」と指示すれば、段階的に安全に進められます。

---

## 8. UI デザイン — ステップ型ウィザード（次世代 UX）

現行 Gradio UI（v0.4.3）は **1画面型**（`assets/mockup.html` 準拠）。配布 UX の次段階として **選択型ステップ UI** を採用する。詳細は [`docs/UI_DESIGN.md`](./docs/UI_DESIGN.md)。

### 8.1 設計の優先順位

静止画の完璧さより **「選んだ後に次の要素がふわっと浮き上がるテンポ感」** を最優先で検証する。

### 8.2 モーション仕様（Figma Smart Animate 想定）

| 項目 | 値 |
|------|-----|
| 形式 | Smart Animate |
| イージング | Ease Out — `cubic-bezier(0, 0, 0.2, 1)` |
| 時間 | **300〜350 ms**（既定 320 ms） |
| 出現 | フェードイン + **下から 24 px** 持ち上げ（20〜30 px レンジ） |
| ステップバー | 上部インジケーター、画面遷移と **同一 duration/easing** で幅を連動 |

### 8.3 ステップ構成（案）

1. ムード（プリセット）→ 2. 楽器 → 3. 自由プロンプト → 4. BPM/長さ/ステップ → 5. 生成・進捗・プレイヤー  
左サイドバー（モデル選択/DL）は全ステップ共通で固定。

### 8.4 検証用アセット

- **`assets/mockup-steps.html`** — ブラウザでクリック操作し、320 ms の浮き上がりとステップバー連動を確認
- **Figma プロトタイプ** — 上記 HTML と同仕様で Smart Animate を設定（チェックリストは `docs/UI_DESIGN.md` §4）

### 8.5 Gradio 実装タイミング

PHASE 4-8 完了後、または PHASE 6 前の **UI リフレッシュ**。推論パス（`MusicGenerator`）はそのまま。Step 5 に v0.4.3 のジェネレータ進捗を配置する。

### 8.6 生成 UX・最適化（PHASE 5 予定）

| 課題 | 対処 |
|------|------|
| UI 初回が 120s×60step で 16 分級 | v0.4.4+: 初回スライダー **30s / 30step**（`LMT_UI_*`）。プリセット選択時のみ長尺値 |
| ACE-Step `ACESTEP_GENERATION_TIMEOUT=600` | 長尺向けに `1800` 等を `.env` / `start_rocm.bat` で設定 |
| float32 + オフロードで遅い | `ACESTEP_ROCM_DTYPE=float16`（VRAM 余裕・速度改善） |
| DCW 無効（`pytorch_wavelets` なし） | 任意: `uv pip install pytorch_wavelets PyWavelets`（torch 版要確認） |
| XL 長尺 | XL Turbo（8 step）またはステップ 30 以下 |