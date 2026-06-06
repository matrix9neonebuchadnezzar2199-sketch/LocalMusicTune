"""ROCm Windows compatibility patches — applied once at startup before ACE-Step imports."""

from __future__ import annotations

import importlib.util
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_PATCH_MARKER = "# lmt-rocm-patch: distributed fallback"

_VQ_OLD = """import torch.distributed as dist
from torch.distributed import nn as dist_nn"""

_VQ_NEW = f"""try:
    import torch.distributed as dist
    from torch.distributed import nn as dist_nn
except (ImportError, AttributeError):
    import types
    dist = types.SimpleNamespace(
        is_initialized=lambda: False,
        get_world_size=lambda: 1,
    )
    dist_nn = None
{_PATCH_MARKER}"""


def apply_rocm_windows_patches() -> None:
    """Patch third-party packages that assume full torch.distributed on ROCm Windows."""
    _patch_vector_quantize_lookup_free()


def _patch_vector_quantize_lookup_free() -> None:
    spec = importlib.util.find_spec("vector_quantize_pytorch")
    if spec is None or not spec.origin:
        return

    target = Path(spec.origin).parent / "lookup_free_quantization.py"
    if not target.is_file():
        return

    text = target.read_text(encoding="utf-8")
    if _PATCH_MARKER in text:
        return

    if _VQ_OLD not in text:
        if "SimpleNamespace" in text and "is_initialized=lambda" in text:
            return
        logger.warning(
            "vector_quantize_pytorch %s: unexpected format, skip ROCm patch",
            target.name,
        )
        return

    target.write_text(text.replace(_VQ_OLD, _VQ_NEW, 1), encoding="utf-8")
    logger.info("Applied ROCm distributed fallback patch to %s", target)
