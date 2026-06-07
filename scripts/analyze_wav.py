"""Quick WAV analysis — peak, RMS, spectral flatness."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import soundfile as sf


def analyze(path: Path) -> dict:
    data, sr = sf.read(path)
    ch = data if data.ndim == 1 else data.mean(axis=1)
    peak = float(np.max(np.abs(ch)))
    rms = float(np.sqrt(np.mean(ch**2)))
    zcr = float(np.mean(np.abs(np.diff(np.sign(ch)))) / 2)
    seg = ch[: min(len(ch), sr * 5)]
    fft = np.abs(np.fft.rfft(seg)) + 1e-12
    flatness = float(np.exp(np.mean(np.log(fft))) / np.mean(fft))
    silent_pct = float(np.mean(np.abs(ch) < 0.001) * 100)
    return {
        "peak": peak,
        "rms": rms,
        "zcr": zcr,
        "flatness": flatness,
        "silent_pct": silent_pct,
        "dur": len(ch) / sr,
    }


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else "outputs")
    for p in sorted(root.glob("*.wav"), key=lambda x: x.stat().st_mtime):
        a = analyze(p)
        print(
            f"{p.name}  dur={a['dur']:.1f}s  peak={a['peak']:.4f}  "
            f"rms={a['rms']:.6f}  flat={a['flatness']:.3f}  "
            f"silent%={a['silent_pct']:.1f}  zcr={a['zcr']:.4f}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
