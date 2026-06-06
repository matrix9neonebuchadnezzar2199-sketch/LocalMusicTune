"""ACE-Step 1.5 model definitions.

Repo IDs verified against the official ACE-Step-1.5 model zoo:
https://github.com/ace-step/ACE-Step-1.5#-model-zoo
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

ModelTier = Literal["standard", "xl", "xl_turbo"]


@dataclass(frozen=True)
class ModelSpec:
    key: str
    display_name: str
    repo_id: str
    weights_size_gb: float
    vram_min_gb: int
    vram_recommended_gb: int
    note: str
    tier: ModelTier
    default: bool = False
    optional: bool = False  # shown in UI but not required for PHASE 3 verification


MODELS: dict[str, ModelSpec] = {
    "ace-1.5-standard": ModelSpec(
        key="ace-1.5-standard",
        display_name="ACE-Step 1.5 標準 (2B)",
        repo_id="ACE-Step/acestep-v15-base",
        weights_size_gb=4.7,
        vram_min_gb=4,
        vram_recommended_gb=8,
        note="軽量・高速試行用。VRAMが少ない環境や手軽に試したいとき向け。",
        tier="standard",
        default=False,
    ),
    "ace-1.5-xl-base": ModelSpec(
        key="ace-1.5-xl-base",
        display_name="ACE-Step 1.5 XL (4B / 高品質)",
        repo_id="ACE-Step/acestep-v15-xl-base",
        weights_size_gb=9.0,
        vram_min_gb=12,
        vram_recommended_gb=20,
        note="高品質。20GB VRAM（例: RX 7900 XT）でオフロードなし運用を想定した既定モデル。",
        tier="xl",
        default=True,
    ),
    "ace-1.5-xl-turbo": ModelSpec(
        key="ace-1.5-xl-turbo",
        display_name="ACE-Step 1.5 XL Turbo (高速 / 8ステップ)",
        repo_id="ACE-Step/acestep-v15-xl-turbo",
        weights_size_gb=9.0,
        vram_min_gb=12,
        vram_recommended_gb=16,
        note="8ステップで高速生成。試行錯誤を繰り返したいときのオプション。",
        tier="xl_turbo",
        optional=True,
    ),
}


def get_model(key: str) -> ModelSpec:
    if key not in MODELS:
        raise KeyError(f"Unknown model key: {key!r}")
    return MODELS[key]


def list_models(*, include_optional: bool = True) -> list[ModelSpec]:
    return [
        m
        for m in MODELS.values()
        if include_optional or not m.optional
    ]


def default_model_key() -> str:
    for spec in MODELS.values():
        if spec.default:
            return spec.key
    return next(iter(MODELS))
