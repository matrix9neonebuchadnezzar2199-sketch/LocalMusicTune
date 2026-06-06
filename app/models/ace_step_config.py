"""ACE-Step config_path mapping and checkpoint layout helpers."""

from __future__ import annotations

import os
import shutil
from pathlib import Path

from app.config import MODELS_DIR, PROJECT_ROOT
from app.models.manager import ModelManager, get_manager

# Official ACE-Step checkpoint folder names (see ACE-Step-1.5 docs/sidestep/Model Management.md)
ACE_STEP_CONFIG_BY_KEY: dict[str, str] = {
    "ace-1.5-standard": "acestep-v15-base",
    "ace-1.5-xl-base": "acestep-v15-xl-base",
    "ace-1.5-xl-turbo": "acestep-v15-xl-turbo",
}

DEFAULT_INFERENCE_STEPS: dict[str, int] = {
    "ace-1.5-standard": 50,
    "ace-1.5-xl-base": 50,
    "ace-1.5-xl-turbo": 8,
}


def is_ace_step_key(model_key: str) -> bool:
    return model_key in ACE_STEP_CONFIG_BY_KEY


def ace_step_config_path(model_key: str) -> str:
    if model_key not in ACE_STEP_CONFIG_BY_KEY:
        raise KeyError(f"Not an ACE-Step model: {model_key!r}")
    return ACE_STEP_CONFIG_BY_KEY[model_key]


def checkpoints_root() -> Path:
    root = Path(os.getenv("ACESTEP_CHECKPOINTS_DIR", PROJECT_ROOT / "checkpoints"))
    root.mkdir(parents=True, exist_ok=True)
    return root


def ensure_ace_step_checkpoint_link(
    model_key: str,
    manager: ModelManager | None = None,
) -> Path:
    """Link LocalMusicTune models/{key} → checkpoints/{acestep-v15-*}."""
    mgr = manager or get_manager()
    if not mgr.is_downloaded(model_key):
        raise FileNotFoundError(
            f"Model {model_key!r} is not downloaded. Use the UI sidebar to download first."
        )
    src = mgr.local_dir(model_key)
    config_name = ace_step_config_path(model_key)
    dest = checkpoints_root() / config_name
    if dest.exists() or dest.is_symlink():
        if dest.is_symlink() and dest.resolve() == src.resolve():
            return dest
        if dest.is_dir() and any(dest.iterdir()):
            return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        if dest.is_symlink():
            dest.unlink()
        elif dest.is_dir() and not any(dest.iterdir()):
            dest.rmdir()
    try:
        os.symlink(src, dest, target_is_directory=True)
    except OSError:
        if dest.exists():
            return dest
        shutil.copytree(src, dest, dirs_exist_ok=True)
    return dest


def ace_step_project_root() -> Path:
    """ACE-Step expects project_root containing checkpoints/."""
    return checkpoints_root().parent
