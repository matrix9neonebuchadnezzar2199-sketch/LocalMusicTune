"""UI helper tests."""

from __future__ import annotations

from app.ui import FIRST_RUN_HINT, _format_generation_progress


def test_format_generation_progress():
    text = _format_generation_progress(5, 20, 0.25, "DiT step 5/20")
    assert "5/20" in text
    assert "25%" in text
    assert "DiT step" in text


def test_first_run_hint_mentions_initial_delay():
    assert "初回" in FIRST_RUN_HINT
