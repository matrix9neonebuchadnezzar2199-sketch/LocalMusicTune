# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- ACE-Step 1.5 inference backend (PHASE 4 — first priority)
- DiffRhythm, YuE, HeartMuLa backends (post ACE-Step)
- One-click launch scripts for ROCm / CUDA on Windows and Linux

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

[Unreleased]: https://github.com/matrix9neonebuchadnezzar2199-sketch/LocalMusicTune/compare/v0.3.2...HEAD
[0.3.2]: https://github.com/matrix9neonebuchadnezzar2199-sketch/LocalMusicTune/compare/v0.3.1...v0.3.2
[0.3.1]: https://github.com/matrix9neonebuchadnezzar2199-sketch/LocalMusicTune/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/matrix9neonebuchadnezzar2199-sketch/LocalMusicTune/releases/tag/v0.3.0
