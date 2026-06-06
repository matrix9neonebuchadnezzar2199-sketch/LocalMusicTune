"""Device detection tests."""

from __future__ import annotations

from app.core.device import DeviceInfo, DeviceKind, detect_device, format_gpu_header, vram_warning_for_model


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


def test_vram_warning_when_insufficient():
    from torch import device as torch_device

    info = DeviceInfo(
        kind=DeviceKind.ROCM,
        device=torch_device("cpu"),
        name="AMD Radeon RX 7600",
        vram_gb=8.0,
        display_label="AMD Radeon",
        mode_label="ROCm",
    )
    warning = vram_warning_for_model(info, vram_min_gb=12)
    assert warning is not None
    assert "12GB" in warning
    assert "8.0GB" in warning


def test_vram_warning_none_when_sufficient():
    from torch import device as torch_device

    info = DeviceInfo(
        kind=DeviceKind.ROCM,
        device=torch_device("cpu"),
        name="AMD Radeon RX 7900 XT",
        vram_gb=20.0,
        display_label="AMD Radeon RX 7900 XT",
        mode_label="ROCm",
    )
    assert vram_warning_for_model(info, vram_min_gb=12) is None
