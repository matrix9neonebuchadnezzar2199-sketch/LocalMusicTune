"""Gradio UI — mockup layout with prompt preview and dummy generation."""

from __future__ import annotations

import time
from typing import Any

import gradio as gr

from app.config import DEFAULT_HOST, DEFAULT_PORT
from app.core.audio import generate_dummy_audio
from app.core.device import DeviceInfo, detect_device, vram_warning_for_model
from app.core.prompt_builder import build_generation_params, format_params_preview
from app.models.backends.capabilities import is_backend_ready
from app.models.manager import DownloadState, get_manager
from app.models.registry import (
    default_model_key,
    format_duration_limit,
    get_model,
    list_models,
)
from app.presets.presets import PRESET_BY_LABEL, PRESET_LABELS

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
.lmt-tag-soon { color: #9aa0b4; font-size: 11px; }
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

PRESET_LABELS_LIST = list(PRESET_LABELS)
DEFAULT_PRESET = PRESET_LABELS_LIST[0]
DEFAULT_PRESET_OBJ = PRESET_BY_LABEL[DEFAULT_PRESET]


def _model_dropdown_update():
    manager = get_manager()
    downloaded = manager.list_downloaded_keys()
    if downloaded:
        choices = [(f"{get_model(k).display_name} ✓保管済み", k) for k in downloaded]
        return gr.update(choices=choices, value=downloaded[0], interactive=True)
    return gr.update(
        choices=[("（保管済みモデルなし — 下からDL）", "")],
        value="",
        interactive=False,
    )


def _resolve_model_key(installed_key: str, dl_key: str) -> str:
    if installed_key:
        return installed_key
    if dl_key:
        return dl_key
    return default_model_key()


def _backend_label(model_key: str) -> str:
    if is_backend_ready(model_key):
        return "推論対応済"
    return "近日対応"


def _format_model_row_html(spec, status: str, manager) -> str:
    if manager.is_downloaded(spec.key):
        tag = '<span class="lmt-tag-ok">保管済み</span>'
    elif manager.get_progress(spec.key).state == DownloadState.DOWNLOADING:
        tag = '<span class="lmt-tag-dl">DL中</span>'
    elif not is_backend_ready(spec.key):
        tag = '<span class="lmt-tag-soon">近日対応</span>'
    elif spec.optional:
        tag = '<span class="lmt-tag-dl">任意</span>'
    else:
        tag = '<span class="lmt-tag-dl">未DL</span>'
    optional = " <em>(任意)</em>" if spec.optional else ""
    max_len = format_duration_limit(spec.max_duration_sec)
    return (
        f'<div class="lmt-model-row">'
        f"<b>{spec.display_name}</b>{optional}<br>"
        f'<span style="color:#9aa0b4;font-size:12px;">'
        f"{spec.license} ／ 約 {spec.weights_size_gb}GB ／ VRAM {spec.vram_min_gb}GB〜 ／ "
        f"最長 {max_len} ／ {_backend_label(spec.key)}<br>"
        f"{spec.good_for}<br>"
        f"— {status}"
        f"</span> {tag}</div>"
    )


def _render_model_management_html() -> str:
    manager = get_manager()
    rows: list[str] = []
    for spec in list_models(include_optional=True):
        status = manager.format_model_status(spec)
        rows.append(_format_model_row_html(spec, status, manager))
    return "\n".join(rows)


def _render_download_progress() -> tuple[str, float]:
    manager = get_manager()
    active = [
        p
        for p in manager.all_progress().values()
        if p.state in (DownloadState.DOWNLOADING, DownloadState.ERROR)
    ]
    if not active:
        return "（ダウンロード待機中）", 0.0
    prog = active[0]
    pct = int(prog.fraction * 100)
    if prog.state == DownloadState.ERROR:
        return f"❌ {prog.error or prog.detail}", 0.0
    spec = get_model(prog.model_key)
    gb_done = spec.weights_size_gb * prog.fraction
    return (
        f"{spec.display_name}: {pct}% — {prog.detail} "
        f"({gb_done:.1f}GB / {spec.weights_size_gb}GB 目安)",
        prog.fraction,
    )


def _refresh_model_panel():
    dd = _model_dropdown_update()
    html = _render_model_management_html()
    progress_label, fraction = _render_download_progress()
    return dd, html, progress_label, fraction


def _start_download(model_key: str):
    if model_key:
        get_manager().start_download(model_key)
    return _refresh_model_panel()


def _vram_warning_text(model_key: str, device_info: DeviceInfo) -> str:
    if not model_key:
        return ""
    spec = get_model(model_key)
    warning = vram_warning_for_model(device_info, spec.vram_min_gb)
    return warning or ""


def _duration_slider_update(model_key: str, current_duration: float):
    if not model_key:
        model_key = default_model_key()
    spec = get_model(model_key)
    max_d = spec.max_duration_sec
    clamped = min(max(float(current_duration), 10), max_d)
    label = f"曲の長さ（秒）— 最大 {format_duration_limit(max_d)}（{spec.display_name}）"
    return gr.Slider(minimum=10, maximum=max_d, value=clamped, step=1, label=label)


def _model_selection_side_effects(model_key: str, current_duration: float, device_info: DeviceInfo):
    if not model_key:
        model_key = default_model_key()
    spec = get_model(model_key)
    dur = _duration_slider_update(model_key, current_duration)
    vram = _vram_warning_text(model_key, device_info)
    detail = (
        f"【{spec.display_name}】 {spec.license} ／ 最長 {format_duration_limit(spec.max_duration_sec)}\n"
        f"{spec.good_for}\n"
        f"推論: {_backend_label(model_key)}"
    )
    return dur, gr.update(value=vram, visible=bool(vram)), detail


def _on_model_pick(model_key: str, cur_duration: float, device_info: DeviceInfo):
    dur, vram_upd, detail = _model_selection_side_effects(model_key, cur_duration, device_info)
    return dur, vram_upd, detail


def _update_preview(
    prompt: str,
    preset: str,
    instruments: list[str],
    bpm: float,
    duration: float,
    steps: float,
) -> str:
    params = build_generation_params(prompt, preset, instruments, bpm, duration, steps)
    return format_params_preview(params)


def _apply_preset_defaults(preset: str) -> tuple[list[str], float, float, float, str]:
    p = PRESET_BY_LABEL[preset]
    params = build_generation_params(
        "",
        preset,
        list(p.default_instruments),
        p.default_bpm,
        p.default_duration_sec,
        p.default_steps,
    )
    return (
        list(p.default_instruments),
        float(p.default_bpm),
        float(p.default_duration_sec),
        float(p.default_steps),
        format_params_preview(params),
    )


def _dummy_generate(
    prompt: str,
    preset: str,
    instruments: list[str],
    bpm: float,
    duration: float,
    steps: float,
    installed_model: str,
    dl_model: str,
    progress: gr.Progress = gr.Progress(),
) -> tuple[str, str | None]:
    """Simulate generation with progress bar; returns audio path."""
    model_key = _resolve_model_key(installed_model, dl_model)
    if not is_backend_ready(model_key):
        spec = get_model(model_key)
        return (
            f"⏳ {spec.display_name} — 推論バックエンドは近日対応です（PHASE 4）。DL と UI 確認のみ可能。",
            None,
        )

    params = build_generation_params(prompt, preset, instruments, bpm, duration, steps)
    total_steps = params.steps
    for i in range(total_steps):
        time.sleep(0.02)
        pct = int((i + 1) / total_steps * 100)
        progress(i / total_steps, desc=f"生成中… {pct}%（ステップ {i + 1} / {total_steps}）")

    out = generate_dummy_audio(duration_sec=min(params.duration_sec, 10.0), silent=False)
    status = f"ダミー生成完了 — {params.preset_id} / {params.bpm}BPM / {params.duration_sec}秒"
    return status, str(out)


def build_ui(device_info: DeviceInfo) -> gr.Blocks:
    init_spec = get_model(default_model_key())
    init_duration_max = init_spec.max_duration_sec
    init_duration_val = min(DEFAULT_PRESET_OBJ.default_duration_sec, init_duration_max)

    with gr.Blocks(title="ローカル音楽生成ツール", css=CUSTOM_CSS, theme=gr.themes.Base()) as demo:
        gr.HTML(
            f"""
            <div class="lmt-header">
              <h1>🎵 ローカル音楽生成ツール</h1>
              <span class="lmt-badge">PHASE 3</span>
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
                        label="保管済みモデルから選択",
                        interactive=False,
                    )
                with gr.Accordion("モデルの管理", open=True):
                    model_mgmt_html = gr.HTML(value=_render_model_management_html())
                    dl_target = gr.Dropdown(
                        label="ダウンロードするモデル",
                        choices=[(m.display_name, m.key) for m in list_models(include_optional=True)],
                        value=default_model_key(),
                    )
                    vram_warning = gr.Textbox(
                        label="VRAM 警告",
                        interactive=False,
                        visible=bool(_vram_warning_text(default_model_key(), device_info)),
                        value=_vram_warning_text(default_model_key(), device_info),
                    )
                    model_detail = gr.Textbox(
                        label="選択モデルの詳細",
                        interactive=False,
                        lines=4,
                        value=(
                            f"【{init_spec.display_name}】 {init_spec.license} ／ "
                            f"最長 {format_duration_limit(init_spec.max_duration_sec)}\n"
                            f"{init_spec.good_for}\n"
                            f"推論: {_backend_label(init_spec.key)}"
                        ),
                    )
                    dl_btn = gr.Button("⬇ 選択モデルをダウンロード", variant="secondary")
                    dl_progress_label = gr.Textbox(
                        label="ダウンロード進捗",
                        interactive=False,
                        value="（ダウンロード待機中）",
                    )
                    dl_progress_bar = gr.Slider(
                        minimum=0,
                        maximum=1,
                        value=0,
                        step=0.01,
                        label="",
                        show_label=False,
                        interactive=False,
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
                        choices=PRESET_LABELS_LIST,
                        value=DEFAULT_PRESET,
                        label="",
                        show_label=False,
                    )

                with gr.Group():
                    gr.Markdown("#### 合成プロンプト（プレビュー）")
                    prompt_preview = gr.Textbox(
                        label="",
                        show_label=False,
                        lines=6,
                        interactive=False,
                        value=_update_preview(
                            "",
                            DEFAULT_PRESET,
                            list(DEFAULT_PRESET_OBJ.default_instruments),
                            DEFAULT_PRESET_OBJ.default_bpm,
                            DEFAULT_PRESET_OBJ.default_duration_sec,
                            DEFAULT_PRESET_OBJ.default_steps,
                        ),
                    )

                with gr.Group():
                    gr.Markdown("#### 楽器")
                    instruments = gr.CheckboxGroup(
                        choices=INSTRUMENTS,
                        value=list(DEFAULT_PRESET_OBJ.default_instruments),
                        label="",
                        show_label=False,
                    )

                with gr.Group():
                    gr.Markdown("#### 詳細設定")
                    bpm = gr.Slider(40, 200, value=DEFAULT_PRESET_OBJ.default_bpm, step=1, label="テンポ (BPM)")
                    duration = gr.Slider(
                        10,
                        init_duration_max,
                        value=init_duration_val,
                        step=1,
                        label=f"曲の長さ（秒）— 最大 {format_duration_limit(init_duration_max)}",
                    )
                    steps = gr.Slider(
                        10, 120, value=DEFAULT_PRESET_OBJ.default_steps, step=1, label="生成ステップ数（品質）"
                    )

                gen_btn = gr.Button("🎶 音楽を生成（ダミー）", variant="primary")

                with gr.Group():
                    gr.Markdown("#### 生成の進捗")
                    progress_text = gr.Textbox(value="待機中", label="進捗", interactive=False)
                    audio_out = gr.Audio(label="生成された曲", type="filepath")

        dl_target.change(
            lambda key, dur: _on_model_pick(key, dur, device_info),
            inputs=[dl_target, duration],
            outputs=[duration, vram_warning, model_detail],
        )

        model_dd.change(
            lambda key, dur: _on_model_pick(key, dur, device_info),
            inputs=[model_dd, duration],
            outputs=[duration, vram_warning, model_detail],
        )

        model_panel_outputs = [model_dd, model_mgmt_html, dl_progress_label, dl_progress_bar]

        dl_btn.click(_start_download, inputs=dl_target, outputs=model_panel_outputs)

        refresh_timer = gr.Timer(value=1.5)
        refresh_timer.tick(_refresh_model_panel, outputs=model_panel_outputs)

        demo.load(_refresh_model_panel, outputs=model_panel_outputs)

        preview_inputs = [prompt, preset, instruments, bpm, duration, steps]
        for component in preview_inputs:
            component.change(_update_preview, inputs=preview_inputs, outputs=prompt_preview)

        preset.change(
            _apply_preset_defaults,
            inputs=preset,
            outputs=[instruments, bpm, duration, steps, prompt_preview],
        )

        gen_btn.click(
            fn=_dummy_generate,
            inputs=[prompt, preset, instruments, bpm, duration, steps, model_dd, dl_target],
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
