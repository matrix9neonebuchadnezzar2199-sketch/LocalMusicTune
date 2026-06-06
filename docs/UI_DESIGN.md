# UI デザイン設計 — LocalMusicTune

本ドキュメントは Gradio 実装（`app/ui.py`）と HTML モック（`assets/`）の**設計の正**です。  
現行 UI（v0.4.3）は1画面型。次世代 UX として**選択型ステップ UI**を採用する方針をここに定義する。

---

## 1. 設計方針

| 優先度 | 内容 |
|--------|------|
| **最優先** | 選択後の**テンポ感** — 次の質問が「ふわっと浮き上がる」遷移 |
| 次点 | 静止画の完璧さより、**モーションの検証** |
| 維持 | 既存モックのダークテーマ（`#0f1117` / `#4a6bff` アクセント） |

参考モック:

- **1画面版（現行）:** `assets/mockup.html`
- **ステップ版（モーション検証）:** `assets/mockup-steps.html` — ブラウザで開いてクリック操作

---

## 2. ステップ UI フロー（案）

生成設定を一度に並べるのではなく、**1画面1問**で進める。

| Step | 画面 | 入力 |
|------|------|------|
| 1 | ムード | プリセット（睡眠 / チル / 集中 …） |
| 2 | 楽器 | チェックボックス（複数可） |
| 3 | イメージ | 自由プロンプト（任意） |
| 4 | 仕上げ | BPM・曲の長さ・生成ステップ数 |
| 5 | 生成 | 合成プレビュー + 生成ボタン + 進捗 + プレイヤー |

**サイドバー（モデル DL / 選択）** は全ステップ共通で左に固定。ステップ遷移はメインカラムのみ。

Gradio 実装フェーズ（未着手）では `gr.Column(visible=…)` の切替 + 共有 CSS トランジション、またはカスタム HTML コンポーネントで近似する。

---

## 3. モーション仕様（Figma Smart Animate 相当）

Figma プロトタイプ作成時の依頼内容を、実装可能な**デザイントークン**として固定する。

### 3.1 画面遷移（選択 → 次の質問）

| 項目 | 値 |
|------|-----|
| アニメーション形式 | Smart Animate（同一レイヤー名の補間） |
| イージング | **Ease Out** — CSS: `cubic-bezier(0, 0, 0.2, 1)` |
| 代替 | Custom Spring / Custom Bezier（後半が滑らかに止まる） |
| 時間 | **300 ms 〜 350 ms**（既定 **320 ms**） |

### 3.2 次画面の出現

- **フェードイン:** `opacity: 0 → 1`
- **持ち上げ:** `translateY(24px) → translateY(0)`（20〜30 px の中央値 **24 px**）
- パッと切り替え（`display: none` の即時切替のみ）は**禁止**

### 3.3 上部ステップインジケーター

- 全幅バー + 「Step n / N」ラベル
- ステップ進行時、バー幅を **同一 duration / easing** でアニメーション
- 生成中（拡散ステップ）の進捗バーとは**別コンポーネント**（混同しない）

### 3.4 CSS トークン（Gradio / HTML 共通）

```css
:root {
  --lmt-motion-duration: 320ms;
  --lmt-motion-ease: cubic-bezier(0, 0, 0.2, 1);
  --lmt-motion-lift: 24px;
}
```

```css
.lmt-step-enter {
  animation: lmt-step-rise var(--lmt-motion-duration) var(--lmt-motion-ease) forwards;
}
@keyframes lmt-step-rise {
  from { opacity: 0; transform: translateY(var(--lmt-motion-lift)); }
  to   { opacity: 1; transform: translateY(0); }
}
```

---

## 4. Figma プロトタイプ作成チェックリスト

デザイナー / 自分用。`assets/mockup-steps.html` の挙動を Figma で再現する。

- [ ] フレーム: Step 1〜4 + 共通ヘッダー + ステップバー
- [ ] 選択肢タップ → **Smart Animate** で次フレームへ
- [ ] 次質問パネル: 下から 24 px + フェードイン（320 ms, Ease Out）
- [ ] ステップバー: 幅が 25% → 50% → … と同一トランジション
- [ ] 戻る操作（任意）: 逆方向は lift を `-12px` 程度に弱めても可
- [ ] プロトタイプ共有リンクを README / Issue に貼る

---

## 5. Gradio 実装へのマッピング（将来）

| Figma / HTML | Gradio 6 |
|--------------|----------|
| Smart Animate 320 ms | カスタム CSS + `gr.HTML` ラッパー、または JS 注入 |
| ステップバー | `gr.Slider`（interactive=False）または HTML バー |
| 選択カード | `gr.Radio` + `elem_classes` / カスタム CSS |
| 非ブロッキング生成 | 既存ジェネレータ（v0.4.3）を Step 5 に配置 |

**PHASE タイミング:** PHASE 4-8 完了後、または PHASE 6（配布準備）前の **UI リフレッシュ** として実装。推論パス（`MusicGenerator`）は変更不要。

---

## 6. 検証方法

1. `assets/mockup-steps.html` をブラウザで開く
2. プリセット → 楽器 → … と選択し、**320 ms の浮き上がり**を目視確認
3. ステップバーが選択と同期して伸びることを確認
4. Figma プロトタイプがあれば HTML と並べてテンポ感を比較

「気持ちいい」と感じるまで `duration`（300–350）や `lift`（20–30 px）を微調整し、本ドキュメント §3 を更新する。
