# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- DiffRhythm, YuE, HeartMuLa inference backends
- One-click launch scripts (PHASE 5)

## [0.4.3] - 2026-06-07

### Added
- Gradio 6: move `css` / `theme` from `gr.Blocks` to `demo.launch()` (mock dark theme restored)
- UI generate button wired to `MusicGenerator.generate` via generator/yield (non-blocking)
- Live diffusion progress: step n/N text + slider; first-run time hint

### Changed
- PHASE 4-4 / 4-5 marked implemented in PLAN.md

## [0.4.2] - 2026-06-07

### Added
- `app/core/patches.py` — auto-patch `vector_quantize_pytorch` distributed import for ROCm Windows
- Offload heuristic: enable CPU offload when VRAM equals model `vram_recommended_gb` (20GB XL fix)

### Fixed
- ROCm Windows: `ImportError: cannot import name 'group' from 'torch.distributed'`
- XL generation on 20GB GPUs: VRAM preflight failure after full GPU model load

## [0.4.1] - 2026-06-07

### Fixed
- Remove `torch` / `torchaudio` from default dependencies so `uv run` no longer overwrites ROCm/CUDA wheels with PyPI CPU builds

### Added
- Optional `[project.optional-dependencies] cpu` extra for CPU-only environments

### Changed
- README / PLAN: PyTorch manual install flow and PHASE 5 startup-script policy

## [0.4.0] - 2026-06-07

PHASE 4 — ACE-Step inference backend with sub-step CLI diagnostics.

### Added
- `AceStepBackend` wrapping official `acestep.inference.generate_music`
- `MusicGenerator` orchestration with VRAM-aware CPU offload
- Checkpoint symlink bridge: `models/` → `checkpoints/acestep-v15-*`
- GPU diagnostics CLI (`uv run lmt-phase4 gpu-diag`) — PHASE 4-1
- ACE load / minimal generate CLI — PHASE 4-2 / 4-3
- UI wired to real generation with Gradio progress adapter
- Dynamic step slider limits for XL Turbo (8-step class)

### Notes
- Requires separate ACE-Step 1.5 package install (Python 3.11–3.12)
- LM thinking disabled by default (`thinking=False`) for simpler first-run path

## [0.3.2] - 2026-06-07

### Added
- Multi-model registry: DiffRhythm full, HeartMuLa 3B, YuE 7B (commercial-use only)
- Model role fields: `good_for`, `max_duration_sec`, `license`, `family`
- UI: per-model license/duration/role display, dynamic duration slider cap
- Backend status label ("近日対応") for models without inference yet
- `NON_COMMERCIAL_MODELS` reference (MusicGen, Stable Audio Open — excluded from UI)

### Changed
- DiffRhythm uses `ASLP-lab/DiffRhythm-1_2-full` (max ~4m45s) instead of base-only
- Generate button blocks with message when backend not ready

## [0.3.1] - 2026-06-07

### Changed
- Default model is now **XL (4B base)** for 20 GB VRAM environments (RX 7900 XT)
- Standard (2B) remains as lightweight / fast-trial option
- UI shows VRAM warning when selected model exceeds detected GPU memory

### Added
- `vram_warning_for_model()` in device module
- PLAN.md §7: finalized model policy and terminology (standard=2B, XL=4B)

## [0.3.0] - 2026-06-07

First public pre-release. UI, prompt pipeline, and model download are functional; inference is placeholder only.

### Added
- Gradio Web UI with dark theme (mockup-aligned layout)
- GPU detection for CUDA, ROCm (AMD Radeon), and CPU fallback
- Seven mood presets: sleep, chill, focus, cafe, workout, game, cinematic
- Prompt builder merging user text, preset style, instruments, and BPM
- Live composed-prompt preview in the UI
- ACE-Step 1.5 model registry (Standard 2B, XL 4B, XL Turbo optional)
- Hugging Face model download with progress polling in the sidebar
- Installed-model scan and dropdown selection
- Configuration via `.env` (paths, port, HF token)
- pytest suite (device, prompt builder, registry, manager)

### Notes
- Generate button returns placeholder audio until v0.4.0 inference backend
- Default `uv sync` installs CPU PyTorch; install GPU build separately for ROCm/CUDA

[Unreleased]: https://github.com/matrix9neonebuchadnezzar2199-sketch/LocalMusicTune/compare/v0.4.3...HEAD
[0.4.3]: https://github.com/matrix9neonebuchadnezzar2199-sketch/LocalMusicTune/compare/v0.4.2...v0.4.3
[0.4.2]: https://github.com/matrix9neonebuchadnezzar2199-sketch/LocalMusicTune/compare/v0.4.1...v0.4.2
[0.4.1]: https://github.com/matrix9neonebuchadnezzar2199-sketch/LocalMusicTune/compare/v0.4.0...v0.4.1
[0.4.0]: https://github.com/matrix9neonebuchadnezzar2199-sketch/LocalMusicTune/compare/v0.3.2...v0.4.0
[0.3.2]: https://github.com/matrix9neonebuchadnezzar2199-sketch/LocalMusicTune/compare/v0.3.1...v0.3.2
[0.3.1]: https://github.com/matrix9neonebuchadnezzar2199-sketch/LocalMusicTune/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/matrix9neonebuchadnezzar2199-sketch/LocalMusicTune/releases/tag/v0.3.0
