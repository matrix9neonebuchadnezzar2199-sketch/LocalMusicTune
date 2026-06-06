"""Preset definitions — sleep / chill / focus / etc."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Preset:
    id: str
    label: str
    emoji: str
    style_prompt: str
    default_bpm: int
    default_instruments: tuple[str, ...]
    default_duration_sec: int
    default_steps: int


PRESETS: tuple[Preset, ...] = (
    Preset(
        id="sleep",
        label="睡眠",
        emoji="😴",
        style_prompt=(
            "very calm, slow, minimal, soft dynamics, no sudden peaks, "
            "ambient atmosphere suitable for falling asleep"
        ),
        default_bpm=60,
        default_instruments=("ピアノ", "パッド"),
        default_duration_sec=180,
        default_steps=50,
    ),
    Preset(
        id="chill",
        label="チル",
        emoji="🌿",
        style_prompt=(
            "relaxed lo-fi chill beat, warm textures, gentle groove, "
            "easy listening background music"
        ),
        default_bpm=75,
        default_instruments=("ギター", "シンセ", "パッド"),
        default_duration_sec=120,
        default_steps=60,
    ),
    Preset(
        id="focus",
        label="集中・作業",
        emoji="📚",
        style_prompt=(
            "steady rhythm, non-distracting, moderate energy, "
            "focus-friendly instrumental without vocals"
        ),
        default_bpm=90,
        default_instruments=("ピアノ", "シンセ", "ドラム"),
        default_duration_sec=120,
        default_steps=60,
    ),
    Preset(
        id="cafe",
        label="カフェ",
        emoji="☕",
        style_prompt=(
            "cozy cafe jazz ambience, acoustic warmth, light swing feel, "
            "pleasant background for conversation"
        ),
        default_bpm=100,
        default_instruments=("ピアノ", "ギター", "ベース"),
        default_duration_sec=120,
        default_steps=60,
    ),
    Preset(
        id="workout",
        label="ワークアウト",
        emoji="🏃",
        style_prompt=(
            "high energy, driving beat, motivational, strong rhythm section, "
            "uptempo electronic or rock elements"
        ),
        default_bpm=130,
        default_instruments=("ドラム", "ベース", "シンセ"),
        default_duration_sec=90,
        default_steps=60,
    ),
    Preset(
        id="game",
        label="ゲーム",
        emoji="🎮",
        style_prompt=(
            "dynamic game soundtrack, engaging loops, clear melody, "
            "adventurous and immersive mood"
        ),
        default_bpm=120,
        default_instruments=("シンセ", "ドラム", "ベース"),
        default_duration_sec=90,
        default_steps=70,
    ),
    Preset(
        id="cinematic",
        label="シネマティック",
        emoji="🎬",
        style_prompt=(
            "cinematic orchestral score, emotional arc, wide dynamics, "
            "film trailer atmosphere, epic but controlled"
        ),
        default_bpm=80,
        default_instruments=("ヴァイオリン", "チェロ", "ピアノ", "パッド"),
        default_duration_sec=150,
        default_steps=80,
    ),
)

PRESET_LABELS: tuple[str, ...] = tuple(f"{p.emoji} {p.label}" for p in PRESETS)

PRESET_BY_LABEL: dict[str, Preset] = {f"{p.emoji} {p.label}": p for p in PRESETS}

PRESET_BY_ID: dict[str, Preset] = {p.id: p for p in PRESETS}
