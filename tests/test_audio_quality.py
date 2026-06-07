"""Tests for audio quality validation."""

from __future__ import annotations

import numpy as np
import soundfile as sf

from app.core.audio_quality import validate_generated_audio


def test_validate_rejects_dc_offset_noise(tmp_path) -> None:
    sr = 48000
    t = np.linspace(0, 1, sr, endpoint=False)
    # One-sided signal mimicking collapsed bfloat16 VAE decode
    wave = 0.5 + 0.2 * np.sin(2 * np.pi * 440 * t)
    path = tmp_path / "bad.wav"
    sf.write(path, wave.astype(np.float32), sr)
    ok, msg = validate_generated_audio(path)
    assert not ok
    assert "片側" in msg


def test_validate_accepts_bipolar_music_like(tmp_path) -> None:
    sr = 48000
    t = np.linspace(0, 1, sr, endpoint=False)
    wave = 0.4 * np.sin(2 * np.pi * 220 * t)
    path = tmp_path / "good.wav"
    sf.write(path, wave.astype(np.float32), sr)
    ok, msg = validate_generated_audio(path)
    assert ok, msg
