"""ACE-Step 1.5 inference backend (PHASE 4)."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

from app.core.audio_quality import validate_generated_audio
from app.core.device import DeviceInfo, vram_warning_for_model
from app.models.ace_step_config import (
    DEFAULT_INFERENCE_STEPS,
    ace_step_config_path,
    ace_step_project_root,
    ensure_ace_step_checkpoint_link,
    is_ace_step_key,
)
from app.models.backends.base import GenerateContext, GenerateResult, LoadResult, noop_progress
from app.models.registry import get_model

logger = logging.getLogger(__name__)


def ace_step_available() -> bool:
    try:
        import acestep  # noqa: F401

        return True
    except ImportError:
        return False


def _resolve_torch_device(device_info: DeviceInfo) -> str:
    if device_info.device.type == "cuda":
        return "cuda"
    return "cpu"


def _estimate_vram_gb() -> float | None:
    try:
        import torch

        if not torch.cuda.is_available():
            return None
        return round(torch.cuda.get_device_properties(0).total_memory / (1024**3), 2)
    except Exception:
        return None


def _should_offload(device_info: DeviceInfo, model_key: str) -> bool:
    spec = get_model(model_key)
    if device_info.vram_gb is None:
        return True
    if vram_warning_for_model(device_info, spec.vram_min_gb):
        return True
    # At exactly recommended VRAM the full model fills the GPU and leaves no
    # headroom for diffusion activations — ACE-Step skips preflight when offload=True.
    return device_info.vram_gb <= spec.vram_recommended_gb


class AceStepBackend:
    """Wraps official acestep.handler + acestep.inference.generate_music."""

    family = "ace_step"

    def __init__(self, device_info: DeviceInfo) -> None:
        self.device_info = device_info
        self._dit_handler: Any = None
        self._llm_handler: Any = None
        self._loaded_key: str | None = None
        self._enable_generate = False

    @property
    def loaded_model_key(self) -> str | None:
        return self._loaded_key

    def load(self, model_key: str, *, device: str | None = None, offload_to_cpu: bool = False) -> LoadResult:
        if not is_ace_step_key(model_key):
            return LoadResult(ok=False, message=f"{model_key} is not an ACE-Step model")
        if not ace_step_available():
            return LoadResult(
                ok=False,
                message=(
                    "ace-step package not installed. Install ACE-Step 1.5 in this environment "
                    "(see README § ACE-Step setup) then retry."
                ),
            )

        from acestep.handler import AceStepHandler
        from acestep.llm_inference import LLMHandler

        if self._loaded_key == model_key and self._dit_handler is not None:
            return LoadResult(ok=True, message=f"Already loaded: {model_key}", vram_gb_used=_estimate_vram_gb())

        self.unload()
        ensure_ace_step_checkpoint_link(model_key)
        config_path = ace_step_config_path(model_key)
        torch_device = device or _resolve_torch_device(self.device_info)
        project_root = str(ace_step_project_root())
        checkpoints = os.path.join(project_root, "checkpoints")

        dit = AceStepHandler()
        init_status, enable_generate = dit.initialize_service(
            project_root=project_root,
            config_path=config_path,
            device=torch_device,
            offload_to_cpu=offload_to_cpu,
        )
        if not enable_generate:
            return LoadResult(ok=False, message=f"DiT load failed: {init_status}")

        llm = LLMHandler()
        lm_path = os.getenv("ACESTEP_LM_MODEL", "acestep-5Hz-lm-0.6B")
        lm_backend = os.getenv("ACESTEP_LM_BACKEND", "pt" if torch_device == "cpu" else "pt")
        lm_status, lm_ok = llm.initialize(
            checkpoint_dir=checkpoints,
            lm_model_path=lm_path,
            backend=lm_backend,
            device=torch_device,
        )
        if not lm_ok:
            logger.warning("LM init failed (%s) — continuing with thinking=False path", lm_status)

        self._dit_handler = dit
        self._llm_handler = llm if lm_ok else None
        self._loaded_key = model_key
        self._enable_generate = enable_generate
        vram = _estimate_vram_gb()
        return LoadResult(
            ok=True,
            message=f"Loaded {config_path} on {torch_device} (offload={offload_to_cpu}). {init_status}",
            vram_gb_used=vram,
        )

    def generate(self, ctx: GenerateContext) -> GenerateResult:
        if not ace_step_available():
            return GenerateResult(ok=False, error="ace-step not installed")
        if self._dit_handler is None or self._loaded_key != ctx.model_key:
            load = self.load(
                ctx.model_key,
                offload_to_cpu=ctx.offload_to_cpu or _should_offload(self.device_info, ctx.model_key),
            )
            if not load.ok:
                return GenerateResult(ok=False, error=load.message)

        from acestep.inference import GenerationConfig, GenerationParams, generate_music

        from app.config import OUTPUTS_DIR, ensure_dirs

        ensure_dirs()
        progress_cb = ctx.progress or noop_progress
        total_steps = int(ctx.params.steps) or DEFAULT_INFERENCE_STEPS.get(ctx.model_key, 50)

        def ace_progress(progress_obj) -> None:
            if progress_obj is None:
                return
            try:
                if hasattr(progress_obj, "progress"):
                    step = int(getattr(progress_obj, "progress", 0) or 0)
                    total = int(getattr(progress_obj, "total", total_steps) or total_steps)
                    progress_cb(
                        step / max(total, 1),
                        step=step,
                        total=total,
                        message=f"DiT step {step}/{total}",
                    )
                elif isinstance(progress_obj, tuple) and len(progress_obj) >= 2:
                    step, total = int(progress_obj[0]), int(progress_obj[1])
                    progress_cb(step / max(total, 1), step=step, total=total)
            except Exception:
                pass

        gen_params = GenerationParams(
            task_type="text2music",
            caption=ctx.params.prompt,
            lyrics="" if ctx.instrumental else "[instrumental]\n",
            instrumental=ctx.instrumental,
            bpm=ctx.params.bpm,
            duration=float(ctx.params.duration_sec),
            inference_steps=total_steps,
            thinking=ctx.thinking and self._llm_handler is not None,
        )
        gen_config = GenerationConfig(
            batch_size=1,
            audio_format="wav",
        )

        wrapped_progress = _GradioStyleProgress(progress_cb, total_steps)

        result = generate_music(
            self._dit_handler,
            self._llm_handler,
            gen_params,
            gen_config,
            save_dir=str(OUTPUTS_DIR),
            progress=wrapped_progress,
        )

        if not getattr(result, "success", False):
            err = getattr(result, "error", None) or "ACE-Step generation failed"
            return GenerateResult(ok=False, error=str(err))

        audios = getattr(result, "audios", None) or []
        if not audios:
            return GenerateResult(ok=False, error="No audio returned from ACE-Step")

        first = audios[0]
        path_str = first.get("path") if isinstance(first, dict) else str(first)
        out = Path(path_str)
        if not out.is_file():
            return GenerateResult(ok=False, error=f"Output file missing: {out}")

        ok_audio, audio_err = validate_generated_audio(out)
        if not ok_audio:
            return GenerateResult(ok=False, error=audio_err, output_path=out)

        return GenerateResult(
            ok=True,
            output_path=out,
            message=f"Generated {out.name} ({ctx.params.duration_sec}s, {total_steps} steps)",
        )

    def unload(self) -> None:
        self._dit_handler = None
        self._llm_handler = None
        self._loaded_key = None
        self._enable_generate = False
        try:
            import gc

            import torch

            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception:
            pass


class _GradioStyleProgress:
    """Adapt ACE-Step progress API to our ProgressCallback."""

    def __init__(self, callback, total_steps: int) -> None:
        self._callback = callback
        self._total = max(total_steps, 1)
        self._current = 0

    def __call__(self, *args, **kwargs) -> None:
        if args:
            if len(args) >= 2 and isinstance(args[0], (int, float)):
                self._current = int(args[0])
                self._total = int(args[1]) if len(args) > 1 else self._total
            elif len(args) == 1 and isinstance(args[0], (int, float)):
                self._current = int(args[0])
        frac = min(self._current / self._total, 1.0)
        self._callback(
            frac,
            step=self._current,
            total=self._total,
            message=kwargs.get("desc", ""),
        )

    def tqdm(self, iterable=None, total=None, **kwargs):
        total = total or self._total
        if iterable is None:
            return iterable
        for i, item in enumerate(iterable, start=1):
            self._current = i
            self._total = total
            self.__call__(i, total)
            yield item
