"""Unit and integration tests for pii-guard CLI."""

import io
import os
import subprocess
import sys
import pytest
from pii_guard.cli import main
from pii_guard.verhoeff import generate_check_digit

FAKE_TEST_KEY = "test-key-not-secret"


def make_valid_aadhaar(prefix_11: str) -> str:
    chk = generate_check_digit(prefix_11)
    return prefix_11 + chk


def test_cli_mask_default_mode(monkeypatch: pytest.MonkeyPatch):
    aadhaar = make_valid_aadhaar("23456789012")
    input_text = f"Contact UID {aadhaar} or mobile 9876543210."
    stdin_stream = io.StringIO(input_text)
    stdout_stream = io.StringIO()
    stderr_stream = io.StringIO()

    monkeypatch.setattr(sys, "stdin", stdin_stream)
    monkeypatch.setattr(sys, "stdout", stdout_stream)
    monkeypatch.setattr(sys, "stderr", stderr_stream)

    exit_code = main(["mask"])
    assert exit_code == 0
    output = stdout_stream.getvalue()
    expected_aadhaar_mask = f"XXXXXXXX{aadhaar[-4:]}"
    assert f"Contact UID {expected_aadhaar_mask} or mobile XXXXXXXX10." in output
    assert stderr_stream.getvalue() == ""


def test_cli_tag_mode_with_key(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("PII_GUARD_KEY", FAKE_TEST_KEY)
    input_text = "PAN is ABCPE1234F."
    stdin_stream = io.StringIO(input_text)
    stdout_stream = io.StringIO()
    stderr_stream = io.StringIO()

    monkeypatch.setattr(sys, "stdin", stdin_stream)
    monkeypatch.setattr(sys, "stdout", stdout_stream)
    monkeypatch.setattr(sys, "stderr", stderr_stream)

    exit_code = main(["mask", "--mode", "tag"])
    assert exit_code == 0
    output = stdout_stream.getvalue()
    assert output.startswith("PAN is [PAN:")
    assert output.endswith("].\n") or output.endswith("].")


def test_cli_tag_mode_fails_closed_without_key(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("PII_GUARD_KEY", raising=False)
    stdin_stream = io.StringIO("PAN is ABCPE1234F.")
    stdout_stream = io.StringIO()
    stderr_stream = io.StringIO()

    monkeypatch.setattr(sys, "stdin", stdin_stream)
    monkeypatch.setattr(sys, "stdout", stdout_stream)
    monkeypatch.setattr(sys, "stderr", stderr_stream)

    exit_code = main(["mask", "--mode", "tag"])
    assert exit_code == 1
    assert "error: PII_GUARD_KEY is not set" in stderr_stream.getvalue()
    # Ensure no partial stdout leaked
    assert stdout_stream.getvalue() == ""


def test_cli_requires_mask_subcommand(monkeypatch: pytest.MonkeyPatch):
    stderr_stream = io.StringIO()
    monkeypatch.setattr(sys, "stderr", stderr_stream)

    exit_code = main([])
    assert exit_code == 2


def test_cli_subprocess_execution():
    # Test that the CLI runs via subprocess across all platforms and environments
    import shutil

    # Try finding pii-guard binary on PATH or adjacent to current python executable
    pii_guard_exe = shutil.which("pii-guard") or shutil.which(
        "pii-guard", path=os.path.dirname(sys.executable)
    )

    if pii_guard_exe:
        cmd = [pii_guard_exe, "mask"]
    else:
        # Cross-platform module execution fallback
        cmd = [sys.executable, "-m", "pii_guard.cli", "mask"]

    proc = subprocess.run(
        cmd,
        input="Call 9876543210 for help.",
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    assert proc.stdout == "Call XXXXXXXX10 for help."
    assert proc.stderr == ""

