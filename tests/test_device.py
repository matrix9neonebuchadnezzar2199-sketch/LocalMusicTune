"""Device detection tests."""

from __future__ import annotations

from app.core.device import DeviceInfo, DeviceKind, detect_device, format_gpu_header


def test_detect_device_returns_device_info():
    info = detect_device()
    assert isinstance(info, DeviceInfo)
    assert info.kind in (DeviceKind.CUDA, DeviceKind.ROCM, DeviceKind.CPU)
    assert info.device is not None
    assert info.display_label
    assert info.mode_label


def test_format_gpu_header():
    from torch import device as torch_device

    info = DeviceInfo(
        kind=DeviceKind.CPU,
        device=torch_device("cpu"),
        name="CPU",
        vram_gb=None,
        display_label="CPU（GPU未検出）",
        mode_label="CPUフォールバック",
    )
    header = format_gpu_header(info)
    assert "CPU" in header
    assert "CPUフォールバック" in header
