"""CLI — PHASE 4 diagnostics and minimal generation tests."""

from __future__ import annotations

import argparse
import sys

from app.core.patches import apply_rocm_windows_patches

apply_rocm_windows_patches()

from app.core.rocm_runtime import apply_rocm_runtime_defaults

apply_rocm_runtime_defaults()

from app.core.device import detect_device
from app.core.generator import MusicGenerator, generate_music_file
from app.core.gpu_diag import format_gpu_diag_report, run_gpu_diagnostics
from app.core.prompt_builder import GenerationParams
from app.models.registry import default_model_key


def cmd_gpu_diag(_args: argparse.Namespace) -> int:
    report = format_gpu_diag_report(run_gpu_diagnostics())
    print(report)
    return 0 if "PASS" in report.splitlines()[-1] else 1


def cmd_ace_load(args: argparse.Namespace) -> int:
    gen = MusicGenerator()
    result = gen.load_model(args.model)
    print(result.message)
    if result.vram_gb_used is not None:
        print(f"VRAM visible: {result.vram_gb_used} GB")
    return 0 if result.ok else 1


def cmd_ace_generate(args: argparse.Namespace) -> int:
    params = GenerationParams(
        prompt=args.prompt,
        preset_id="cli",
        bpm=args.bpm,
        duration_sec=args.duration,
        steps=args.steps,
        instruments=(),
    )

    def progress(frac: float, *, step: int, total: int, message: str = "") -> None:
        pct = int(frac * 100)
        print(f"\r{pct:3d}% step {step}/{total} {message}", end="", flush=True)

    try:
        out = generate_music_file(
            args.model,
            params,
            progress=progress if args.verbose else None,
        )
        print(f"\nSaved: {out}")
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"\nError: {exc}", file=sys.stderr)
        return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="LocalMusicTune PHASE 4 CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p_diag = sub.add_parser("gpu-diag", help="PHASE 4-1 GPU/ROCm diagnostics")
    p_diag.set_defaults(func=cmd_gpu_diag)

    p_load = sub.add_parser("ace-load", help="PHASE 4-2 load ACE-Step model only")
    p_load.add_argument("--model", default="ace-1.5-standard")
    p_load.set_defaults(func=cmd_ace_load)

    p_gen = sub.add_parser("ace-generate", help="PHASE 4-3 minimal ACE-Step generation")
    p_gen.add_argument("--model", default="ace-1.5-standard")
    p_gen.add_argument("--prompt", default="calm ambient piano, soft and minimal")
    p_gen.add_argument("--duration", type=int, default=10)
    p_gen.add_argument("--steps", type=int, default=20)
    p_gen.add_argument("--bpm", type=int, default=90)
    p_gen.add_argument("-v", "--verbose", action="store_true")
    p_gen.set_defaults(func=cmd_ace_generate)

    args = parser.parse_args(argv)
    print(f"Device: {detect_device().display_label}")
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
