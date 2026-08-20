"""Tests for the load_secrets() function in accessibility_mgr.app.

Covers: file parsing, comment handling, blank-line handling, whitespace
stripping (FUN-013), equals-in-values preservation (SEC-002), malformed
line skipping, missing-file error, and auto-setup integration.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest


@pytest.fixture()
def secrets_dir(tmp_path, monkeypatch):
    """Change the working directory to a tmp folder so load_secrets()
    reads/writes ``.secrets`` there instead of the real repo root."""
    monkeypatch.chdir(tmp_path)
    return tmp_path


def _write_secrets(directory: Path, content: str) -> None:
    (directory / ".secrets").write_text(content)


class TestLoadPopulatesEnv:
    def test_reads_valid_file(self, secrets_dir, monkeypatch):
        _write_secrets(secrets_dir, "MY_KEY=my_value\nOTHER_KEY=other_value\n")
        from accessibility_mgr.app import load_secrets

        load_secrets()
        assert os.environ.get("MY_KEY") == "my_value"
        assert os.environ.get("OTHER_KEY") == "other_value"

        monkeypatch.delenv("MY_KEY", raising=False)
        monkeypatch.delenv("OTHER_KEY", raising=False)


class TestLoadSkipsComments:
    def test_comment_lines_not_loaded(self, secrets_dir, monkeypatch):
        _write_secrets(
            secrets_dir,
            "# This is a comment\nKEY=value\n# Another comment\n",
        )
        from accessibility_mgr.app import load_secrets

        load_secrets()
        assert os.environ.get("KEY") == "value"
        assert os.environ.get("# This is a comment") is None  # noqa: SIM112

        monkeypatch.delenv("KEY", raising=False)


class TestLoadSkipsBlankLines:
    def test_blank_lines_not_loaded(self, secrets_dir, monkeypatch):
        _write_secrets(
            secrets_dir,
            "A=1\n\n\nB=2\n\n",
        )
        from accessibility_mgr.app import load_secrets

        load_secrets()
        assert os.environ.get("A") == "1"
        assert os.environ.get("B") == "2"

        monkeypatch.delenv("A", raising=False)
        monkeypatch.delenv("B", raising=False)


class TestLoadPreservesEqualsInValues:
    def test_base64_value_with_equals(self, secrets_dir, monkeypatch):
        value_with_equals = "abc123=="
        _write_secrets(secrets_dir, f"TOKEN={value_with_equals}\n")
        from accessibility_mgr.app import load_secrets

        load_secrets()
        assert os.environ.get("TOKEN") == value_with_equals

        monkeypatch.delenv("TOKEN", raising=False)


class TestLoadStripsWhitespace:
    def test_strips_spaces_around_key_and_value(self, secrets_dir, monkeypatch):
        _write_secrets(secrets_dir, "  MY_KEY  =  my_value  \n")
        from accessibility_mgr.app import load_secrets

        load_secrets()
        assert os.environ.get("MY_KEY") == "my_value"

        monkeypatch.delenv("MY_KEY", raising=False)


class TestLoadSkipsMalformedLines:
    def test_line_without_equals_skipped(self, secrets_dir, monkeypatch):
        _write_secrets(secrets_dir, "GOOD=value\nNOEqualsHere\nALSO_GOOD=x\n")
        from accessibility_mgr.app import load_secrets

        load_secrets()
        assert os.environ.get("GOOD") == "value"
        assert os.environ.get("ALSO_GOOD") == "x"
        assert os.environ.get("NOEqualsHere") is None  # noqa: SIM112

        monkeypatch.delenv("GOOD", raising=False)
        monkeypatch.delenv("ALSO_GOOD", raising=False)


class TestLoadRaisesWhenMissing:
    def test_file_not_found_error(self, secrets_dir):
        from accessibility_mgr.app import load_secrets

        with pytest.raises(FileNotFoundError, match="Secrets file"):
            load_secrets()


class TestLoadAutoRunsSetup:
    def test_setup_invoked_when_secrets_missing(self, secrets_dir, monkeypatch):
        """When .secrets is missing and setup.py exists, subprocess.run
        should be called with the setup script path."""
        from accessibility_mgr.app import load_secrets

        calls = []

        def fake_run(cmd, **kwargs):
            calls.append(cmd)

        monkeypatch.setattr("subprocess.run", fake_run)
        monkeypatch.setattr(
            "accessibility_mgr.app._base_path",
            lambda: secrets_dir,
        )
        (secrets_dir / "setup.py").write_text("# stub\n")

        with pytest.raises(FileNotFoundError, match="Run 'python setup.py'"):
            load_secrets()

        assert len(calls) == 1
        assert "setup.py" in str(calls[0])

    def test_setup_not_invoked_when_secrets_exist(self, secrets_dir, monkeypatch):
        """When .secrets already exists, setup.py should NOT be invoked."""
        from accessibility_mgr.app import load_secrets

        _write_secrets(secrets_dir, "KEY=val\n")
        (secrets_dir / "setup.py").write_text("# stub\n")

        calls = []
        monkeypatch.setattr("subprocess.run", lambda cmd, **kw: calls.append(cmd))

        load_secrets()
        assert len(calls) == 0

        monkeypatch.delenv("KEY", raising=False)
