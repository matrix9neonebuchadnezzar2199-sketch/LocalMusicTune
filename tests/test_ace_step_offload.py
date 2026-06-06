"""ACE-Step backend offload heuristics."""

from __future__ import annotations

from app.core.device import DeviceInfo, DeviceKind
from app.models.backends.ace_step import _should_offload


def _rocm_info(vram_gb: float) -> DeviceInfo:
    from torch import device as torch_device

    return DeviceInfo(
        kind=DeviceKind.ROCM,
        device=torch_device("cuda"),
        name="AMD Radeon RX 7900 XT",
        vram_gb=vram_gb,
        display_label="test",
        mode_label="ROCm",
    )


def test_offload_when_vram_equals_recommended():
    assert _should_offload(_rocm_info(20.0), "ace-1.5-xl-base") is True


def test_no_offload_when_vram_above_recommended():
    assert _should_offload(_rocm_info(24.0), "ace-1.5-xl-base") is False
