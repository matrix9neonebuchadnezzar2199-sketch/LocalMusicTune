"""GPU diagnostics tests."""

from __future__ import annotations

from app.core.gpu_diag import format_gpu_diag_report, run_gpu_diagnostics


def test_gpu_diag_runs():
    result = run_gpu_diagnostics()
    assert result.device_info is not None
    report = format_gpu_diag_report(result)
    assert "GPU Diagnostics" in report
    assert "detect_device()" in report


def test_gpu_diag_tensor_test_runs():
    result = run_gpu_diagnostics()
    assert isinstance(result.tensor_on_device_ok, bool)
