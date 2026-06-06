"""Gradio UI — mockup layout with dummy generation (PHASE 1)."""

from __future__ import annotations

import time
from typing import Any

import gradio as gr

from app.config import DEFAULT_HOST, DEFAULT_PORT
from app.core.audio import generate_dummy_audio
from app.core.device import DeviceInfo, detect_device

# Dark theme CSS aligned with assets/mockup.html
CUSTOM_CSS = """
:root {
  --bg: #0f1117;
  --panel: #1a1d27;
  --panel2: #232735;
  --accent: #6c8cff;
  --accent2: #4a6bff;
  --text: #e8eaf0;
  --muted: #9aa0b4;
  --border: #2c3142;
}
.gradio-container { background: var(--bg) !important; max-width: 100% !important; }
footer { display: none !important; }
.lmt-header {
  padding: 14px 28px;
  background: linear-gradient(90deg, #1a1d27, #232735);
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 0;
}
.lmt-header h1 { font-size: 18px; margin: 0; color: var(--text); }
.lmt-badge {
  font-size: 12px;
  background: var(--accent2);
  color: #fff;
  padding: 3px 10px;
  border-radius: 12px;
}
.lmt-gpu-info {
  margin-left: auto;
  font-size: 12px;
  color: var(--muted);
  background: var(--panel2);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 8px 14px;
}
.lmt-sidebar-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--muted);
  margin-bottom: 8px;
}
.lmt-model-row {
  background: var(--panel2);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 10px 12px;
  margin-bottom: 8px;
  font-size: 13px;
}
.lmt-tag-ok { color: #6ee7a0; font-size: 11px; }
.lmt-tag-dl { color: #e7d06e; font-size: 11px; }
"""

INSTRUMENTS = [
    "ピアノ",
    "ヴァイオリン",
    "ギター",
    "ドラム",
    "ベース",
    "シンセ",
    "フルート",
    "チェロ",
    "パッド",
]

PRESET_LABELS = [
    "😴 睡眠",
    "🌿 チル",
    "📚 集中・作業",
    "☕ カフェ",
    "🏃 ワークアウト",
    "🎮 ゲーム",
    "🎬 シネマティック",
]

DUMMY_MODELS = [
    ("ACE-Step 1.5 標準 (2B)", "未DL（PHASE 3で接続）"),
    ("ACE-Step 1.5 XL (4B)", "未DL（PHASE 3で接続）"),
]


def _dummy_generate(
    prompt: str,
    preset: str,
    instruments: list[str],
    bpm: float,
    duration: float,
    steps: float,
    progress: gr.Progress = gr.Progress(),
) -> tuple[str, str | None]:
    """Simulate generation with progress bar; returns audio path."""
    total_steps = int(steps)
    for i in range(total_steps):
        time.sleep(0.02)
        pct = int((i + 1) / total_steps * 100)
        progress(i / total_steps, desc=f"生成中… {pct}%（ステップ {i + 1} / {total_steps}）")

    out = generate_dummy_audio(duration_sec=min(duration, 10.0), silent=False)
    status = (
        f"ダミー生成完了（PHASE 1）— BPM:{int(bpm)} / 長さ:{int(duration)}秒 / "
        f"ステップ:{total_steps} / プリセット:{preset} / 楽器:{', '.join(instruments) or 'なし'}"
    )
    if prompt.strip():
        status += f" / プロンプト:{prompt[:60]}{'…' if len(prompt) > 60 else ''}"
    return status, str(out)


def build_ui(device_info: DeviceInfo) -> gr.Blocks:
    with gr.Blocks(title="ローカル音楽生成ツール", css=CUSTOM_CSS, theme=gr.themes.Base()) as demo:
        gr.HTML(
            f"""
            <div class="lmt-header">
              <h1>🎵 ローカル音楽生成ツール</h1>
              <span class="lmt-badge">PHASE 1</span>
              <div class="lmt-gpu-info">
                検出GPU: <b style="color:#6ee7a0;">{device_info.display_label}</b>
                ／ 起動モード: {device_info.mode_label}
              </div>
            </div>
            """
        )

        with gr.Row():
            with gr.Column(scale=1, min_width=280):
                gr.Markdown("### モデル設定", elem_classes=["lmt-sidebar-title"])
                with gr.Accordion("使用するモデル", open=True):
                    model_dd = gr.Dropdown(
                        choices=["（PHASE 3 — 保管済みモデル未接続）"],
                        value="（PHASE 3 — 保管済みモデル未接続）",
                        label="保管済みモデルから選択",
                        interactive=False,
                    )
                with gr.Accordion("モデルの管理", open=True):
                    for name, meta in DUMMY_MODELS:
                        gr.Markdown(
                            f'<div class="lmt-model-row">{name}<br>'
                            f'<span style="color:#9aa0b4;font-size:12px;">{meta}</span> '
                            f'<span class="lmt-tag-dl">未DL</span></div>'
                        )

            with gr.Column(scale=2):
                with gr.Group():
                    gr.Markdown("#### イメージ（プロンプト）")
                    prompt = gr.Textbox(
                        label="どんな曲にしたいか自由に入力してください",
                        placeholder="例：静かな雨の夜に合う、落ち着いたローファイヒップホップ…",
                        lines=4,
                    )

                with gr.Group():
                    gr.Markdown("#### プリセット")
                    preset = gr.Radio(
                        choices=PRESET_LABELS,
                        value=PRESET_LABELS[0],
                        label="",
                        show_label=False,
                    )

                with gr.Group():
                    gr.Markdown("#### 楽器")
                    instruments = gr.CheckboxGroup(
                        choices=INSTRUMENTS,
                        value=["ピアノ", "ギター"],
                        label="",
                        show_label=False,
                    )

                with gr.Group():
                    gr.Markdown("#### 詳細設定")
                    bpm = gr.Slider(40, 200, value=90, step=1, label="テンポ (BPM)")
                    duration = gr.Slider(10, 300, value=120, step=1, label="曲の長さ（秒）")
                    steps = gr.Slider(10, 120, value=60, step=1, label="生成ステップ数（品質）")

                gen_btn = gr.Button("🎶 音楽を生成（ダミー）", variant="primary")

                with gr.Group():
                    gr.Markdown("#### 生成の進捗")
                    progress_text = gr.Textbox(value="待機中", label="進捗", interactive=False)
                    audio_out = gr.Audio(label="生成された曲", type="filepath")

        gen_btn.click(
            fn=_dummy_generate,
            inputs=[prompt, preset, instruments, bpm, duration, steps],
            outputs=[progress_text, audio_out],
        )

    return demo


def launch(device_info: DeviceInfo | None = None, **kwargs: Any) -> None:
    info = device_info or detect_device()
    demo = build_ui(info)
    demo.launch(
        server_name=kwargs.get("server_name", DEFAULT_HOST),
        server_port=kwargs.get("server_port", DEFAULT_PORT),
        share=kwargs.get("share", False),
    )
