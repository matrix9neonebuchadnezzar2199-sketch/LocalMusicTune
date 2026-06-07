"""Post-generation audio sanity checks."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import soundfile as sf


def validate_generated_audio(path: Path) -> tuple[bool, str]:
    """Return (ok, error_message). Detect silent / DC-offset / noise-like output."""
    if not path.is_file():
        return False, f"出力ファイルがありません: {path}"

    try:
        data, _sr = sf.read(path)
    except Exception as exc:  # noqa: BLE001
        return False, f"WAV を読めません: {exc}"

    ch = data if data.ndim == 1 else data.mean(axis=1)
    if ch.size == 0:
        return False, "出力が空です。"

    peak = float(np.max(np.abs(ch)))
    if peak < 0.15:
        return False, (
            f"生成結果がほぼ無音です (peak={peak:.3f})。"
            " bfloat16 で長尺×多ステップのときに起きます。"
            " ステップを 30 以下にするか ACESTEP_ROCM_DTYPE=float32 で再試行してください。"
        )

    # Collapsed VAE decode: waveform stays on one side of zero (zcr≈0).
    if ch.min() >= -1e-4 or ch.max() <= 1e-4:
        return False, (
            "波形が片側のみ（VAE デコード異常）。"
            " bfloat16 + 長尺 + 多ステップの組み合わせが原因のことが多いです。"
            " ACESTEP_ROCM_DTYPE=float32 またはステップ数を下げて再生成してください。"
        )

    seg = ch[: min(len(ch), 48000 * 5)]
    fft = np.abs(np.fft.rfft(seg)) + 1e-12
    flatness = float(np.exp(np.mean(np.log(fft))) / np.mean(fft))
    if flatness > 0.35 and peak > 0.3:
        return False, (
            f"ノイズ状の出力です (spectral flatness={flatness:.2f})。"
            " 正規化で無音に近い信号が増幅された可能性があります。"
            " float32 またはステップ 30 以下で再試行してください。"
        )

    return True, ""
