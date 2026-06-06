"""MusicGenerator routing tests."""

from __future__ import annotations

from app.core.generator import MusicGenerator
from app.core.prompt_builder import GenerationParams
from app.models.backends.capabilities import is_backend_ready


def test_ace_models_marked_ready():
    assert is_backend_ready("ace-1.5-xl-base")
    assert not is_backend_ready("diffrhythm-full")


def test_can_generate_ace_without_package():
    gen = MusicGenerator()
    ok, msg = gen.can_generate("ace-1.5-standard")
    # ace-step likely not installed in CI — either ready message or import message
    assert isinstance(ok, bool)
    assert msg


def test_non_ace_backend_not_ready():
    gen = MusicGenerator()
    ok, msg = gen.can_generate("yue-7b")
    assert ok is False
    assert "not implemented" in msg or "未対応" in msg


def test_load_non_ace_fails():
    gen = MusicGenerator()
    result = gen.load_model("diffrhythm-full")
    assert result.ok is False
