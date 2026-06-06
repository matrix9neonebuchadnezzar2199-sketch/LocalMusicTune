"""Application entry point — launches Gradio UI."""

from __future__ import annotations

from app.config import ensure_dirs
from app.core.device import detect_device
from app.ui import launch


def main() -> None:
    ensure_dirs()
    device = detect_device()
    print(f"LocalMusicTune — {device.display_label} ({device.mode_label})")
    launch(device_info=device)


if __name__ == "__main__":
    main()
