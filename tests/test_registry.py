"""Model registry tests."""

from __future__ import annotations

import pytest

from app.models.registry import (
    MODELS,
    NON_COMMERCIAL_MODELS,
    default_model_key,
    get_model,
    list_models,
    list_models_by_family,
)


def test_models_contain_all_commercial_families():
    keys = set(MODELS)
    assert "ace-1.5-xl-base" in keys
    assert "diffrhythm-full" in keys
    assert "heartmula-3b" in keys
    assert "yue-7b" in keys


def test_xl_base_is_default():
    assert default_model_key() == "ace-1.5-xl-base"
    assert get_model(default_model_key()).default is True


def test_diffrhythm_full_max_duration():
    spec = get_model("diffrhythm-full")
    assert spec.max_duration_sec == 285
    assert spec.repo_id == "ASLP-lab/DiffRhythm-1_2-full"
    assert spec.license == "Apache-2.0"


def test_heartmula_repo_id():
    spec = get_model("heartmula-3b")
    assert spec.repo_id == "HeartMuLa/HeartMuLa-oss-3B"
    assert spec.optional is True


def test_ace_models_backend_ready():
    assert get_model("ace-1.5-standard").backend_ready is True
    assert get_model("ace-1.5-xl-base").backend_ready is True
    assert not get_model("diffrhythm-full").backend_ready


def test_optional_models():
    optional = {m.key for m in list_models(include_optional=True) if m.optional}
    assert optional == {"ace-1.5-xl-turbo", "heartmula-3b"}
    core_count = len(list_models(include_optional=False))
    assert core_count == 4


def test_non_commercial_documented():
    names = {m.key for m in NON_COMMERCIAL_MODELS}
    assert "musicgen" in names
    assert "stable-audio-open" in names


def test_list_models_by_family():
    ace = list_models_by_family("ace_step")
    assert len(ace) == 3
    assert all(m.family == "ace_step" for m in ace)


def test_unknown_model_raises():
    with pytest.raises(KeyError):
        get_model("nonexistent")
