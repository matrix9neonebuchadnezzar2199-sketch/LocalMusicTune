"""Application entry point — launches Gradio UI."""

from __future__ import annotations

from app.config import DEFAULT_HOST, DEFAULT_PORT, ensure_dirs


def main() -> None:
    ensure_dirs()
    # UI wiring added in PHASE 1+
    from app.config import MODELS_DIR, OUTPUTS_DIR

    print("LocalMusicTune scaffold ready (PHASE 0).")
    print(f"  models:  {MODELS_DIR}")
    print(f"  outputs: {OUTPUTS_DIR}")
    print(f"  Run PHASE 1+ to start Gradio UI on {DEFAULT_HOST}:{DEFAULT_PORT}")


if __name__ == "__main__":
    main()
