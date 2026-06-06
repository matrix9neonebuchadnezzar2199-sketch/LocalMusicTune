"""Tests for ROCm Windows startup patches."""

from __future__ import annotations

from pathlib import Path

from app.core.patches import (
    _PATCH_MARKER,
    _VQ_NEW,
    _VQ_OLD,
    _patch_vector_quantize_lookup_free,
)


def test_vector_quantize_patch_replaces_import(tmp_path: Path, monkeypatch) -> None:
    pkg = tmp_path / "vector_quantize_pytorch"
    pkg.mkdir()
    target = pkg / "lookup_free_quantization.py"
    target.write_text(f"# header\n{_VQ_OLD}\n\nimport torch\n", encoding="utf-8")

    class FakeSpec:
        origin = str(pkg / "__init__.py")

    monkeypatch.setattr(
        "app.core.patches.importlib.util.find_spec",
        lambda name: FakeSpec() if name == "vector_quantize_pytorch" else None,
    )
    monkeypatch.setattr("app.core.patches.Path", lambda p: target if str(p).endswith("lookup_free_quantization.py") else Path(p))

    # Patch via direct call with real path
    import importlib.util

    def fake_find_spec(name: str):
        if name == "vector_quantize_pytorch":
            spec = importlib.util.spec_from_file_location(name, pkg / "__init__.py")
            assert spec is not None
            spec.origin = str(pkg / "__init__.py")
            return spec
        return None

    monkeypatch.setattr("app.core.patches.importlib.util.find_spec", fake_find_spec)
    _patch_vector_quantize_lookup_free()

    text = target.read_text(encoding="utf-8")
    assert _PATCH_MARKER in text
    assert _VQ_OLD not in text
    assert "SimpleNamespace" in text

    # Second call is no-op
    before = text
    _patch_vector_quantize_lookup_free()
    assert target.read_text(encoding="utf-8") == before
