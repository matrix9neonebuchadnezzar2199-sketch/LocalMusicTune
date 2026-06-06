"""ACE-Step checkpoint mapping tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.models.ace_step_config import (
    ACE_STEP_CONFIG_BY_KEY,
    ace_step_config_path,
    checkpoints_root,
    is_ace_step_key,
)


def test_config_paths():
    assert ace_step_config_path("ace-1.5-standard") == "acestep-v15-base"
    assert ace_step_config_path("ace-1.5-xl-base") == "acestep-v15-xl-base"
    assert ace_step_config_path("ace-1.5-xl-turbo") == "acestep-v15-xl-turbo"


def test_is_ace_step_key():
    assert is_ace_step_key("ace-1.5-xl-base")
    assert not is_ace_step_key("diffrhythm-full")


def test_checkpoints_root_under_project(tmp_path, monkeypatch):
    monkeypatch.setenv("ACESTEP_CHECKPOINTS_DIR", str(tmp_path / "ckpt"))
    assert checkpoints_root() == tmp_path / "ckpt"


def test_unknown_key_raises():
    with pytest.raises(KeyError):
        ace_step_config_path("unknown")


def test_all_ace_keys_mapped():
    for key in ("ace-1.5-standard", "ace-1.5-xl-base", "ace-1.5-xl-turbo"):
        assert key in ACE_STEP_CONFIG_BY_KEY
