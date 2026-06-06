"""PHASE 4-1 — GPU / ROCm environment diagnostics (no model load)."""

from __future__ import annotations

from dataclasses import dataclass

import torch

from app.core.device import DeviceInfo, detect_device


@dataclass(frozen=True)
class GpuDiagResult:
    ok: bool
    device_info: DeviceInfo
    torch_cuda_available: bool
    tensor_on_device_ok: bool
    messages: tuple[str, ...]


def run_gpu_diagnostics() -> GpuDiagResult:
    """Verify PyTorch sees the GPU and can run a tiny matmul."""
    info = detect_device()
    messages: list[str] = []
    cuda_ok = torch.cuda.is_available()
    messages.append(f"torch.cuda.is_available() = {cuda_ok}")
    messages.append(f"detect_device() = {info.display_label} / {info.mode_label}")

    if cuda_ok:
        try:
            name = torch.cuda.get_device_name(0)
            props = torch.cuda.get_device_properties(0)
            vram = round(props.total_memory / (1024**3), 1)
            messages.append(f"GPU[0] = {name}, VRAM = {vram} GB")
            if getattr(torch.version, "hip", None):
                messages.append(f"ROCm (HIP) = {torch.version.hip}")
        except Exception as exc:  # noqa: BLE001
            messages.append(f"GPU property query failed: {exc}")

    tensor_ok = False
    try:
        dev = info.device if cuda_ok else torch.device("cpu")
        a = torch.randn(64, 64, device=dev)
        b = torch.randn(64, 64, device=dev)
        _ = (a @ b).sum().item()
        tensor_ok = True
        messages.append(f"Matmul test on {dev} succeeded")
    except Exception as exc:  # noqa: BLE001
        messages.append(f"Matmul test failed: {exc}")

    ok = tensor_ok and (cuda_ok or info.kind.value == "cpu")
    if info.kind.value == "cpu" and not cuda_ok:
        messages.append("CPU fallback path available (slow generation expected)")
        ok = tensor_ok

    return GpuDiagResult(
        ok=ok,
        device_info=info,
        torch_cuda_available=cuda_ok,
        tensor_on_device_ok=tensor_ok,
        messages=tuple(messages),
    )


def format_gpu_diag_report(result: GpuDiagResult) -> str:
    lines = ["=== LocalMusicTune GPU Diagnostics (PHASE 4-1) ==="]
    lines.extend(result.messages)
    lines.append(f"Overall: {'PASS' if result.ok else 'FAIL'}")
    return "\n".join(lines)
