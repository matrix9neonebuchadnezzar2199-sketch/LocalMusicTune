# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- ACE-Step 1.5 inference backend (real music generation)
- One-click launch scripts for ROCm / CUDA on Windows and Linux
- VRAM warnings when selecting models too large for detected GPU

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

[Unreleased]: https://github.com/matrix9neonebuchadnezzar2199-sketch/LocalMusicTune/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/matrix9neonebuchadnezzar2199-sketch/LocalMusicTune/releases/tag/v0.3.0
