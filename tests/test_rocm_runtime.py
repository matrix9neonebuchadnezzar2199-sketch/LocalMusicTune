"""Tests for ROCm bfloat16 quality-risk heuristics."""

from __future__ import annotations

import os

import torch

from app.core.device import DeviceInfo, DeviceKind
from app.core.rocm_runtime import rocm_bfloat16_quality_risk


def _rocm_info() -> DeviceInfo:
    return DeviceInfo(
        kind=DeviceKind.ROCM,
        device=torch.device("cuda"),
        name="Test GPU",
        vram_gb=20.0,
        display_label="AMD Test",
        mode_label="ROCm",
    )


def test_risky_when_bfloat16_long_and_many_steps(monkeypatch) -> None:
    monkeypatch.setenv("ACESTEP_ROCM_DTYPE", "bfloat16")
    risky, msg = rocm_bfloat16_quality_risk(_rocm_info(), 30, 60)
    assert risky
    assert "float32" in msg


def test_safe_when_short_or_few_steps(monkeypatch) -> None:
    monkeypatch.setenv("ACESTEP_ROCM_DTYPE", "bfloat16")
    assert not rocm_bfloat16_quality_risk(_rocm_info(), 30, 20)[0]
    assert not rocm_bfloat16_quality_risk(_rocm_info(), 20, 60)[0]


def test_ignored_on_cuda(monkeypatch) -> None:
    monkeypatch.setenv("ACESTEP_ROCM_DTYPE", "bfloat16")
    cuda = DeviceInfo(
        kind=DeviceKind.CUDA,
        device=torch.device("cuda"),
        name="NVIDIA",
        vram_gb=24.0,
        display_label="NVIDIA",
        mode_label="CUDA",
    )
    assert not rocm_bfloat16_quality_risk(cuda, 30, 60)[0]
