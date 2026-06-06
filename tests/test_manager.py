"""Model manager tests (local scan, no network)."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.models.manager import ModelManager
from app.models.registry import get_model


@pytest.fixture
def temp_manager(tmp_path: Path) -> ModelManager:
    return ModelManager(models_dir=tmp_path / "models")


def test_is_downloaded_false_when_empty(temp_manager: ModelManager):
    assert not temp_manager.is_downloaded("ace-1.5-standard")


def test_is_downloaded_true_with_marker_file(temp_manager: ModelManager):
    key = "ace-1.5-standard"
    model_dir = temp_manager.local_dir(key)
    model_dir.mkdir(parents=True)
    (model_dir / "config.json").write_text("{}", encoding="utf-8")
    assert temp_manager.is_downloaded(key)


def test_list_downloaded_keys(temp_manager: ModelManager):
    key = "ace-1.5-standard"
    model_dir = temp_manager.local_dir(key)
    model_dir.mkdir(parents=True)
    (model_dir / "model.safetensors").write_bytes(b"x")
    assert temp_manager.list_downloaded_keys() == [key]


def test_format_model_status(temp_manager: ModelManager):
    spec = get_model("ace-1.5-standard")
    assert temp_manager.format_model_status(spec) == "未DL"
