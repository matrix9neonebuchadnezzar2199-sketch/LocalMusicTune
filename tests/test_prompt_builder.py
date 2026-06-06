"""Prompt builder tests."""

from __future__ import annotations

import pytest

from app.core.prompt_builder import build_generation_params, format_params_preview
from app.presets.presets import PRESET_BY_LABEL, PRESET_LABELS


def test_build_generation_params_includes_user_and_preset():
    label = PRESET_LABELS[0]  # sleep
    params = build_generation_params(
        user_prompt="静かな雨の夜",
        preset_label=label,
        instruments=["ピアノ", "パッド"],
        bpm=60,
        duration_sec=120,
        steps=50,
    )
    assert "静かな雨の夜" in params.prompt
    assert "Style:" in params.prompt
    assert "60 BPM" in params.prompt
    assert params.preset_id == PRESET_BY_LABEL[label].id
    assert params.instruments == ("ピアノ", "パッド")


def test_build_generation_params_uses_preset_defaults_when_no_instruments():
    label = "🌿 チル"
    params = build_generation_params(
        user_prompt="",
        preset_label=label,
        instruments=[],
        bpm=75,
        duration_sec=120,
        steps=60,
    )
    preset = PRESET_BY_LABEL[label]
    assert params.instruments == preset.default_instruments
    assert "chill" in params.prompt.lower() or "lo-fi" in params.prompt.lower()


def test_format_params_preview():
    params = build_generation_params(
        user_prompt="test",
        preset_label=PRESET_LABELS[2],
        instruments=["ギター"],
        bpm=100,
        duration_sec=90,
        steps=60,
    )
    preview = format_params_preview(params)
    assert "【合成プロンプト】" in preview
    assert "test" in preview
    assert "bpm=100" in preview


def test_unknown_preset_raises():
    with pytest.raises(KeyError):
        build_generation_params("x", "invalid", [], 90, 120, 60)
