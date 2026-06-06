"""GPU detection (CUDA / ROCm / CPU) with CPU fallback."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import torch


class DeviceKind(str, Enum):
    CUDA = "cuda"
    ROCM = "rocm"
    CPU = "cpu"


@dataclass(frozen=True)
class DeviceInfo:
    kind: DeviceKind
    device: torch.device
    name: str
    vram_gb: float | None
    display_label: str
    mode_label: str


def _vram_gb() -> float | None:
    if not torch.cuda.is_available():
        return None
    try:
        props = torch.cuda.get_device_properties(0)
        return round(props.total_memory / (1024**3), 1)
    except Exception:
        return None


def _is_rocm() -> bool:
    if getattr(torch.version, "hip", None) is not None:
        return True
    if torch.cuda.is_available():
        name = torch.cuda.get_device_name(0).upper()
        if "AMD" in name or "RADEON" in name:
            return True
    return False


def detect_device() -> DeviceInfo:
    """Detect the best available compute device."""
    if torch.cuda.is_available():
        name = torch.cuda.get_device_name(0)
        vram = _vram_gb()
        if _is_rocm():
            label = f"AMD {name} (ROCm)"
            if vram is not None:
                label = f"AMD Radeon (ROCm) — {name}, {vram}GB VRAM"
            return DeviceInfo(
                kind=DeviceKind.ROCM,
                device=torch.device("cuda"),
                name=name,
                vram_gb=vram,
                display_label=label,
                mode_label="ROCm版で動作中",
            )
        vram_suffix = f", {vram}GB VRAM" if vram is not None else ""
        return DeviceInfo(
            kind=DeviceKind.CUDA,
            device=torch.device("cuda"),
            name=name,
            vram_gb=vram,
            display_label=f"NVIDIA {name} (CUDA){vram_suffix}",
            mode_label="CUDA版で動作中",
        )

    return DeviceInfo(
        kind=DeviceKind.CPU,
        device=torch.device("cpu"),
        name="CPU",
        vram_gb=None,
        display_label="CPU（GPU未検出）",
        mode_label="CPUフォールバック",
    )


def format_gpu_header(info: DeviceInfo) -> str:
    """Single-line GPU summary for the UI header."""
    return f"検出GPU: **{info.display_label}** ／ 起動モード: {info.mode_label}"
