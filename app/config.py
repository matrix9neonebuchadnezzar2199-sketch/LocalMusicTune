"""Central configuration: paths, constants, environment overrides."""

from __future__ import annotations

import os
from pathlib import Path

# Project root (LocalMusicTune/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Default directories (overridable via .env)
MODELS_DIR = Path(os.getenv("LMT_MODELS_DIR", PROJECT_ROOT / "models"))
OUTPUTS_DIR = Path(os.getenv("LMT_OUTPUTS_DIR", PROJECT_ROOT / "outputs"))

# Gradio server
DEFAULT_PORT = int(os.getenv("LMT_PORT", "7860"))
DEFAULT_HOST = os.getenv("LMT_HOST", "127.0.0.1")

# UI generation defaults (first paint — not preset values; avoids 120s/60step on first click)
UI_DEFAULT_DURATION_SEC = int(os.getenv("LMT_UI_DURATION_SEC", "30"))
UI_DEFAULT_STEPS = int(os.getenv("LMT_UI_STEPS", "30"))


def ensure_dirs() -> None:
    """Create models/ and outputs/ if they do not exist."""
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
