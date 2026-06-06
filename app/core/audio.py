"""Audio output helpers — dummy generation for PHASE 1."""

from __future__ import annotations

import time
from pathlib import Path

import numpy as np
import soundfile as sf

from app.config import DEFAULT_CHANNELS, DEFAULT_SAMPLE_RATE, OUTPUTS_DIR, ensure_dirs


def generate_dummy_audio(
    duration_sec: float = 3.0,
    *,
    silent: bool = False,
    frequency_hz: float = 440.0,
) -> Path:
    """Write a placeholder WAV file (silent or short sine tone)."""
    ensure_dirs()
    sample_count = int(DEFAULT_SAMPLE_RATE * duration_sec)
    t = np.linspace(0, duration_sec, sample_count, endpoint=False)

    if silent:
        samples = np.zeros((sample_count, DEFAULT_CHANNELS), dtype=np.float32)
    else:
        wave = 0.25 * np.sin(2 * np.pi * frequency_hz * t)
        samples = np.stack([wave, wave], axis=1).astype(np.float32)

    out_path = OUTPUTS_DIR / f"dummy_{int(time.time())}.wav"
    sf.write(out_path, samples, DEFAULT_SAMPLE_RATE)
    return out_path
