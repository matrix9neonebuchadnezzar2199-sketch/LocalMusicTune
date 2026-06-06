"""Model download, local scan, and progress tracking."""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from huggingface_hub import hf_hub_download, list_repo_files

from app.config import MODELS_DIR, ensure_dirs
from app.models.registry import MODELS, ModelSpec, get_model


class DownloadState(str, Enum):
    IDLE = "idle"
    DOWNLOADING = "downloading"
    COMPLETE = "complete"
    ERROR = "error"


@dataclass
class DownloadProgress:
    model_key: str
    state: DownloadState = DownloadState.IDLE
    fraction: float = 0.0
    detail: str = ""
    error: str | None = None


@dataclass
class ModelManager:
    models_dir: Path = field(default_factory=lambda: MODELS_DIR)
    _progress: dict[str, DownloadProgress] = field(default_factory=dict)
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def __post_init__(self) -> None:
        ensure_dirs()
        self.models_dir.mkdir(parents=True, exist_ok=True)

    def local_dir(self, model_key: str) -> Path:
        return self.models_dir / model_key

    def is_downloaded(self, model_key: str) -> bool:
        path = self.local_dir(model_key)
        if not path.is_dir():
            return False
        markers = (
            list(path.rglob("*.safetensors"))
            + list(path.rglob("*.bin"))
            + list(path.rglob("config.json"))
            + list(path.rglob("model_index.json"))
        )
        return len(markers) > 0

    def list_downloaded_keys(self) -> list[str]:
        return [key for key in MODELS if self.is_downloaded(key)]

    def get_progress(self, model_key: str) -> DownloadProgress:
        with self._lock:
            return self._progress.get(
                model_key,
                DownloadProgress(model_key=model_key),
            )

    def all_progress(self) -> dict[str, DownloadProgress]:
        with self._lock:
            return dict(self._progress)

    def _set_progress(self, prog: DownloadProgress) -> None:
        with self._lock:
            self._progress[prog.model_key] = prog

    def start_download(self, model_key: str) -> DownloadProgress:
        spec = get_model(model_key)
        current = self.get_progress(model_key)
        if current.state == DownloadState.DOWNLOADING:
            return current
        if self.is_downloaded(model_key):
            done = DownloadProgress(
                model_key=model_key,
                state=DownloadState.COMPLETE,
                fraction=1.0,
                detail="すでに保管済み",
            )
            self._set_progress(done)
            return done

        prog = DownloadProgress(
            model_key=model_key,
            state=DownloadState.DOWNLOADING,
            fraction=0.0,
            detail="準備中…",
        )
        self._set_progress(prog)
        thread = threading.Thread(
            target=self._download_worker,
            args=(spec,),
            daemon=True,
            name=f"dl-{model_key}",
        )
        thread.start()
        return prog

    def _download_worker(self, spec: ModelSpec) -> None:
        model_key = spec.key
        dest = self.local_dir(model_key)
        dest.mkdir(parents=True, exist_ok=True)
        try:
            files = [
                f
                for f in list_repo_files(spec.repo_id)
                if not f.endswith("/")
            ]
            total = max(len(files), 1)
            for idx, filename in enumerate(files):
                self._set_progress(
                    DownloadProgress(
                        model_key=model_key,
                        state=DownloadState.DOWNLOADING,
                        fraction=idx / total,
                        detail=f"DL中 ({idx + 1}/{total}): {filename}",
                    )
                )
                hf_hub_download(
                    repo_id=spec.repo_id,
                    filename=filename,
                    local_dir=str(dest),
                )
            self._set_progress(
                DownloadProgress(
                    model_key=model_key,
                    state=DownloadState.COMPLETE,
                    fraction=1.0,
                    detail="ダウンロード完了",
                )
            )
        except Exception as exc:  # noqa: BLE001 — surface to UI
            self._set_progress(
                DownloadProgress(
                    model_key=model_key,
                    state=DownloadState.ERROR,
                    fraction=0.0,
                    detail="エラー",
                    error=str(exc),
                )
            )

    def delete_model(self, model_key: str) -> bool:
        import shutil

        path = self.local_dir(model_key)
        if not path.exists():
            return False
        shutil.rmtree(path)
        with self._lock:
            self._progress.pop(model_key, None)
        return True

    def format_model_status(self, spec: ModelSpec) -> str:
        if self.is_downloaded(spec.key):
            return "保管済み"
        prog = self.get_progress(spec.key)
        if prog.state == DownloadState.DOWNLOADING:
            pct = int(prog.fraction * 100)
            return f"DL中 {pct}% — {prog.detail}"
        if prog.state == DownloadState.ERROR:
            return f"エラー: {prog.error or prog.detail}"
        return "未DL"


# Shared singleton for UI session
_manager: ModelManager | None = None


def get_manager() -> ModelManager:
    global _manager
    if _manager is None:
        _manager = ModelManager()
    return _manager
