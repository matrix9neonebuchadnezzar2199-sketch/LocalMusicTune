"""Model registry — commercial-use models (MIT / Apache-2.0) by role.

Repo IDs verified against official sources before listing.
Non-commercial models (MusicGen, Stable Audio Open) are documented separately.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

ModelFamily = Literal["ace_step", "diffrhythm", "heartmula", "yue"]
LicenseKind = Literal["MIT", "Apache-2.0"]


@dataclass(frozen=True)
class ModelSpec:
    key: str
    display_name: str
    repo_id: str
    license: LicenseKind
    weights_size_gb: float
    vram_min_gb: int
    vram_recommended_gb: int
    max_duration_sec: int
    good_for: str
    family: ModelFamily
    default: bool = False
    optional: bool = False
    backend_ready: bool = False  # True when backends/ implements inference


@dataclass(frozen=True)
class NonCommercialModelNote:
    """Reference only — not offered for download in the UI."""

    key: str
    display_name: str
    license_note: str
    max_duration_sec: int | None
    reason_excluded: str


MODELS: dict[str, ModelSpec] = {
    # --- ACE-Step 1.5（主軸 / MIT）https://github.com/ace-step/ACE-Step-1.5 ---
    "ace-1.5-standard": ModelSpec(
        key="ace-1.5-standard",
        display_name="ACE-Step 1.5 標準 (2B)",
        repo_id="ACE-Step/acestep-v15-base",
        license="MIT",
        weights_size_gb=4.7,
        vram_min_gb=4,
        vram_recommended_gb=8,
        max_duration_sec=240,
        good_for="万能。歌もインストも。軽くて速い。手軽に試す用。",
        family="ace_step",
    ),
    "ace-1.5-xl-base": ModelSpec(
        key="ace-1.5-xl-base",
        display_name="ACE-Step 1.5 XL (4B / 高品質)",
        repo_id="ACE-Step/acestep-v15-xl-base",
        license="MIT",
        weights_size_gb=9.0,
        vram_min_gb=12,
        vram_recommended_gb=20,
        max_duration_sec=240,
        good_for="高品質な万能型。RX 7900 XT 等 20GB クラスの主軸。",
        family="ace_step",
        default=True,
    ),
    "ace-1.5-xl-turbo": ModelSpec(
        key="ace-1.5-xl-turbo",
        display_name="ACE-Step 1.5 XL Turbo (高速 / 8ステップ)",
        repo_id="ACE-Step/acestep-v15-xl-turbo",
        license="MIT",
        weights_size_gb=9.0,
        vram_min_gb=12,
        vram_recommended_gb=16,
        max_duration_sec=240,
        good_for="高速生成。何曲も試行錯誤したいとき。",
        family="ace_step",
        optional=True,
    ),
    # --- DiffRhythm（Apache-2.0）https://github.com/ASLP-lab/DiffRhythm ---
    "diffrhythm-full": ModelSpec(
        key="diffrhythm-full",
        display_name="DiffRhythm (超高速フルソング / 最大4分45秒)",
        repo_id="ASLP-lab/DiffRhythm-1_2-full",
        license="Apache-2.0",
        weights_size_gb=6.0,
        vram_min_gb=8,
        vram_recommended_gb=12,
        max_duration_sec=285,
        good_for="歌+伴奏のフルソングを爆速生成。再生時間最長クラス。",
        family="diffrhythm",
    ),
    # --- HeartMuLa（Apache-2.0）https://github.com/HeartMuLa/HeartLib ---
    "heartmula-3b": ModelSpec(
        key="heartmula-3b",
        display_name="HeartMuLa 3B (話題の新顔)",
        repo_id="HeartMuLa/HeartMuLa-oss-3B",
        license="Apache-2.0",
        weights_size_gb=8.0,
        vram_min_gb=8,
        vram_recommended_gb=16,
        max_duration_sec=360,
        good_for="歌モノに強い新顔。推論時は HeartCodec 等の追加权重が必要（PHASE 4+）。",
        family="heartmula",
        optional=True,
    ),
    # --- YuE（Apache-2.0）---
    "yue-7b": ModelSpec(
        key="yue-7b",
        display_name="YuE 7B (長尺・歌詞重視 / 低速)",
        repo_id="m-a-p/YuE-s1-7B-anneal-en-icl",
        license="Apache-2.0",
        weights_size_gb=14.0,
        vram_min_gb=10,
        vram_recommended_gb=16,
        max_duration_sec=300,
        good_for="歌詞から本格フルソング。表現力重視。生成は遅め。",
        family="yue",
    ),
}

# 配布ツールの既定候補から除外（README 参照用のみ）
NON_COMMERCIAL_MODELS: tuple[NonCommercialModelNote, ...] = (
    NonCommercialModelNote(
        key="musicgen",
        display_name="MusicGen (Meta)",
        license_note="CC BY-NC 4.0（非商用）",
        max_duration_sec=30,
        reason_excluded="商用利用不可。1回約30秒の短尺BGM向け。",
    ),
    NonCommercialModelNote(
        key="stable-audio-open",
        display_name="Stable Audio Open",
        license_note="Stability AI Community License",
        max_duration_sec=47,
        reason_excluded="一定規模以上の商用利用に制限。非商用枠としてのみ言及。",
    ),
)


def get_model(key: str) -> ModelSpec:
    if key not in MODELS:
        raise KeyError(f"Unknown model key: {key!r}")
    return MODELS[key]


def list_models(*, include_optional: bool = True) -> list[ModelSpec]:
    return [m for m in MODELS.values() if include_optional or not m.optional]


def list_models_by_family(family: ModelFamily) -> list[ModelSpec]:
    return [m for m in MODELS.values() if m.family == family]


def default_model_key() -> str:
    for spec in MODELS.values():
        if spec.default:
            return spec.key
    return next(iter(MODELS))


def format_duration_limit(sec: int) -> str:
    if sec >= 60:
        minutes = sec // 60
        rem = sec % 60
        if rem:
            return f"{minutes}分{rem}秒"
        return f"{minutes}分"
    return f"{sec}秒"
