"""Music generation orchestration — model load, backend dispatch, progress."""

from __future__ import annotations

import logging
from pathlib import Path

from app.core.device import DeviceInfo, detect_device, vram_warning_for_model
from app.core.prompt_builder import GenerationParams
from app.models.ace_step_config import is_ace_step_key
from app.models.backends.ace_step import AceStepBackend, ace_step_available
from app.models.backends.base import GenerateContext, GenerateResult, LoadResult, ProgressCallback
from app.models.backends.capabilities import is_backend_ready
from app.models.registry import get_model

logger = logging.getLogger(__name__)


class MusicGenerator:
    """Single entry for UI / CLI — routes ACE-Step family to AceStepBackend."""

    def __init__(self, device_info: DeviceInfo | None = None) -> None:
        self.device_info = device_info or detect_device()
        self._ace = AceStepBackend(self.device_info)

    def vram_warning(self, model_key: str) -> str | None:
        spec = get_model(model_key)
        return vram_warning_for_model(self.device_info, spec.vram_min_gb)

    def can_generate(self, model_key: str) -> tuple[bool, str]:
        if not is_backend_ready(model_key):
            return False, "推論バックエンド未対応"
        spec = get_model(model_key)
        if spec.family == "ace_step":
            if not ace_step_available():
                return False, "ace-step パッケージ未インストール（README 参照）"
            return True, "ACE-Step ready"
        return False, f"{spec.family} backend not implemented yet"

    def load_model(self, model_key: str, *, force_offload: bool | None = None) -> LoadResult:
        if not is_ace_step_key(model_key):
            return LoadResult(ok=False, message=f"No backend for {model_key}")
        offload = force_offload
        if offload is None:
            from app.models.backends.ace_step import _should_offload

            offload = _should_offload(self.device_info, model_key)
        return self._ace.load(model_key, offload_to_cpu=offload)

    def generate(
        self,
        model_key: str,
        params: GenerationParams,
        *,
        progress: ProgressCallback | None = None,
        instrumental: bool = True,
        thinking: bool = False,
    ) -> GenerateResult:
        ok, reason = self.can_generate(model_key)
        if not ok:
            return GenerateResult(ok=False, error=reason)

        from app.models.backends.ace_step import _should_offload

        ctx = GenerateContext(
            model_key=model_key,
            params=params,
            progress=progress,
            instrumental=instrumental,
            thinking=thinking,
            offload_to_cpu=_should_offload(self.device_info, model_key),
        )

        if is_ace_step_key(model_key):
            return self._ace.generate(ctx)

        return GenerateResult(ok=False, error=f"Unsupported model: {model_key}")

    def unload(self) -> None:
        self._ace.unload()


def generate_music_file(
    model_key: str,
    params: GenerationParams,
    *,
    device_info: DeviceInfo | None = None,
    progress: ProgressCallback | None = None,
) -> Path:
    """CLI helper — raises on failure."""
    gen = MusicGenerator(device_info)
    result = gen.generate(model_key, params, progress=progress)
    if not result.ok or result.output_path is None:
        raise RuntimeError(result.error or result.message or "Generation failed")
    return result.output_path
