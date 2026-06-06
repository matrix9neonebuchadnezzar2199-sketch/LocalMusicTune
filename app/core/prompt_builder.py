"""Prompt composition from UI inputs (instruments / BPM / preset)."""

from __future__ import annotations

from dataclasses import dataclass

from app.presets.presets import PRESET_BY_LABEL, Preset


@dataclass(frozen=True)
class GenerationParams:
    """Final prompt and generation parameters for the model backend."""

    prompt: str
    preset_id: str
    bpm: int
    duration_sec: int
    steps: int
    instruments: tuple[str, ...]


def resolve_preset(preset_label: str) -> Preset:
    if preset_label not in PRESET_BY_LABEL:
        raise KeyError(f"Unknown preset label: {preset_label!r}")
    return PRESET_BY_LABEL[preset_label]


def build_generation_params(
    user_prompt: str,
    preset_label: str,
    instruments: list[str] | tuple[str, ...],
    bpm: int | float,
    duration_sec: int | float,
    steps: int | float,
) -> GenerationParams:
    """Merge user input, preset style, instruments, and BPM into one prompt."""
    preset = resolve_preset(preset_label)
    inst = tuple(instruments) if instruments else preset.default_instruments
    bpm_i = int(bpm)
    duration_i = int(duration_sec)
    steps_i = int(steps)

    parts: list[str] = []
    text = user_prompt.strip()
    if text:
        parts.append(text)
    parts.append(f"Style: {preset.style_prompt}.")
    if inst:
        parts.append(f"Featured instruments: {', '.join(inst)}.")
    parts.append(f"Tempo: approximately {bpm_i} BPM.")
    parts.append(f"Preset mood: {preset.label}.")

    return GenerationParams(
        prompt=" ".join(parts),
        preset_id=preset.id,
        bpm=bpm_i,
        duration_sec=duration_i,
        steps=steps_i,
        instruments=inst,
    )


def format_params_preview(params: GenerationParams) -> str:
    """Human-readable preview for UI debug panel."""
    return (
        f"【合成プロンプト】\n{params.prompt}\n\n"
        f"【パラメータ】 preset={params.preset_id}, bpm={params.bpm}, "
        f"duration={params.duration_sec}s, steps={params.steps}, "
        f"instruments={', '.join(params.instruments)}"
    )
