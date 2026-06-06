"""Which model keys have an inference backend implemented."""

from __future__ import annotations

from app.models.registry import get_model

# ACE-Step family — PHASE 4
BACKEND_READY_KEYS: frozenset[str] = frozenset(
    {
        "ace-1.5-standard",
        "ace-1.5-xl-base",
        "ace-1.5-xl-turbo",
    }
)


def is_backend_ready(model_key: str) -> bool:
    if model_key in BACKEND_READY_KEYS:
        return True
    try:
        return get_model(model_key).backend_ready
    except KeyError:
        return False
