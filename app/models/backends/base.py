"""Abstract inference backend interface."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Protocol

from app.core.prompt_builder import GenerationParams


class ProgressCallback(Protocol):
    """Report diffusion progress (fraction 0..1, step detail)."""

    def __call__(
        self,
        fraction: float,
        *,
        step: int,
        total: int,
        message: str = "",
    ) -> None: ...


@dataclass(frozen=True)
class LoadResult:
    ok: bool
    message: str
    vram_gb_used: float | None = None


@dataclass(frozen=True)
class GenerateResult:
    ok: bool
    output_path: Path | None = None
    message: str = ""
    error: str | None = None


@dataclass
class GenerateContext:
    """Runtime options passed to backends."""

    model_key: str
    params: GenerationParams
    progress: ProgressCallback | None = None
    instrumental: bool = True
    thinking: bool = False
    offload_to_cpu: bool = False
    extra: dict = field(default_factory=dict)


class InferenceBackend(Protocol):
    family: str

    def load(self, model_key: str, *, device: str, offload_to_cpu: bool = False) -> LoadResult: ...

    def generate(self, ctx: GenerateContext) -> GenerateResult: ...

    def unload(self) -> None: ...


def noop_progress(fraction: float, *, step: int, total: int, message: str = "") -> None:
    del fraction, step, total, message


def gradio_progress_adapter(progress_obj) -> ProgressCallback:
    """Adapt Gradio Progress tracker to ProgressCallback."""

    def _cb(fraction: float, *, step: int, total: int, message: str = "") -> None:
        desc = message or f"生成中… {int(fraction * 100)}%（ステップ {step} / {total}）"
        progress_obj(fraction, desc=desc)

    return _cb
