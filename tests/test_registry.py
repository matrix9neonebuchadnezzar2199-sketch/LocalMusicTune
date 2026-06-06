"""Model registry tests."""

from __future__ import annotations

import pytest

from app.models.registry import MODELS, default_model_key, get_model, list_models


def test_models_contain_standard_and_xl():
    keys = set(MODELS)
    assert "ace-1.5-standard" in keys
    assert "ace-1.5-xl-base" in keys


def test_standard_is_default():
    assert default_model_key() == "ace-1.5-standard"
    assert get_model(default_model_key()).default is True


def test_standard_repo_id():
    spec = get_model("ace-1.5-standard")
    assert spec.repo_id == "ACE-Step/acestep-v15-base"
    assert spec.vram_min_gb == 4


def test_xl_turbo_is_optional():
    turbo = get_model("ace-1.5-xl-turbo")
    assert turbo.optional is True
    core = list_models(include_optional=False)
    assert all(not m.optional for m in core)
    assert len(core) == 2


def test_unknown_model_raises():
    with pytest.raises(KeyError):
        get_model("nonexistent")
