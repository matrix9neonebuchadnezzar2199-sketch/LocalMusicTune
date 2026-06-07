"""ROCm runtime defaults and bfloat16 quality-risk heuristics (RX 7900 XT)."""

from __future__ import annotations

import os

from app.core.device import DeviceInfo, DeviceKind

# bfloat16 + long latent + many diffusion steps collapses on ROCm Windows
# (peak ~0.003 before norm → loud noise after normalize). Verified 2026-06-07:
#   OK: 30s×20step, 20s×60step, 10s×20step
#   NG: 30s×60step (same as UI sleep preset at 60 steps)
_BFLOAT16_RISK_PRODUCT = 1500  # duration_sec * steps; 30×50=1500 borderline


def apply_rocm_runtime_defaults() -> None:
    """Set safe ROCm env defaults when the user has not configured them."""
    if os.getenv("HSA_OVERRIDE_GFX_VERSION") is None:
        os.environ["HSA_OVERRIDE_GFX_VERSION"] = "11.0.0"
    if os.getenv("ACESTEP_LM_BACKEND") is None:
        os.environ["ACESTEP_LM_BACKEND"] = "pt"
    if os.getenv("MIOPEN_FIND_MODE") is None:
        os.environ["MIOPEN_FIND_MODE"] = "FAST"
    if os.getenv("ACESTEP_INIT_LLM") is None:
        os.environ["ACESTEP_INIT_LLM"] = "false"
    # ACE-Step defaults ROCm to float32; we do not override ACESTEP_ROCM_DTYPE here —
    # caller may set bfloat16 for speed when steps×duration is modest.


def active_rocm_dtype() -> str:
    return os.getenv("ACESTEP_ROCM_DTYPE", "float32").strip().lower()


def rocm_bfloat16_quality_risk(
    device_info: DeviceInfo,
    duration_sec: int,
    steps: int,
) -> tuple[bool, str]:
    """Return (is_risky, user_message) for bfloat16 on ROCm."""
    if device_info.kind != DeviceKind.ROCM:
        return False, ""
    if active_rocm_dtype() not in ("bfloat16", "bf16"):
        return False, ""

    product = duration_sec * steps
    if product < _BFLOAT16_RISK_PRODUCT:
        return False, ""

    msg = (
        f"bfloat16 では {duration_sec}秒×{steps}ステップは音質が崩れることがあります"
        f"（duration×steps={product}）。"
        " 対処: ステップを 30 以下に下げる、または "
        "PowerShell で `$env:ACESTEP_ROCM_DTYPE='float32'` を設定してから再生成してください。"
        " float16 は ROCm 上で NaN になるため非推奨です。"
    )
    return True, msg


def format_rocm_dtype_hint(device_info: DeviceInfo) -> str:
    if device_info.kind != DeviceKind.ROCM:
        return ""
    dtype = active_rocm_dtype()
    if dtype in ("bfloat16", "bf16"):
        return f"ROCm dtype={dtype}（高速。長尺×多ステップは float32 推奨）"
    return f"ROCm dtype={dtype}"
