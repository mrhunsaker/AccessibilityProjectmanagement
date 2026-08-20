"""Tests for the SetupAssistant class in setup.py.

Covers: secret generation, password hashing, .secrets file creation,
file permissions, validation, tools.ini setup, and OS detection.
"""

from __future__ import annotations

import base64
import hashlib
import os
from pathlib import Path

import pytest


@pytest.fixture()
def assistant(tmp_path):
    """Create a SetupAssistant pointed at a temporary directory."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from setup import SetupAssistant

    a = SetupAssistant()
    a.repo_root = tmp_path
    a.secrets_file = tmp_path / ".secrets"
    a.tools_example = tmp_path / "tools.ini.example"
    a.tools_file = tmp_path / "tools.ini"
    return a


class TestGenerateStorageSecret:
    def test_returns_nonempty_string(self, assistant):
        result = assistant.generate_storage_secret()
        assert isinstance(result, str)
        assert len(result) > 0

    def test_returns_urlsafe_chars(self, assistant):
        result = assistant.generate_storage_secret()
        safe_chars = set(
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            "abcdefghijklmnopqrstuvwxyz"
            "0123456789"
            "-_"
        )
        assert all(c in safe_chars for c in result)

    def test_unique_on_each_call(self, assistant):
        results = {assistant.generate_storage_secret() for _ in range(10)}
        assert len(results) == 10


class TestGeneratePasswordHash:
    def test_returns_base64_string(self, assistant):
        result = assistant.generate_password_hash("testpassword")
        raw = base64.b64decode(result)
        assert isinstance(raw, bytes)
        assert len(raw) == 48  # 16-byte salt + 32-byte derived key

    def test_different_passwords_produce_different_hashes(self, assistant):
        h1 = assistant.generate_password_hash("password1")
        h2 = assistant.generate_password_hash("password2")
        assert h1 != h2

    def test_same_password_produces_different_hashes_due_to_random_salt(
        self, assistant
    ):
        h1 = assistant.generate_password_hash("same_password")
        h2 = assistant.generate_password_hash("same_password")
        assert h1 != h2


class TestCreateSecretsFile:
    def test_creates_file_with_required_keys(self, assistant, monkeypatch):
        monkeypatch.setattr(
            "setup.getpass.getpass", lambda prompt: "testpassword"
        )
        monkeypatch.setattr("builtins.input", lambda prompt: "")

        result = assistant.create_secrets_file()
        assert result is True
        assert assistant.secrets_file.exists()

        content = assistant.secrets_file.read_text()
        assert "STORAGE_SECRET=" in content
        assert "ACCESSMAN_PASSWORD_HASH=" in content

    def test_sets_unix_permissions(self, assistant, monkeypatch):
        if assistant.is_windows:
            pytest.skip("permissions test is Unix-only")

        monkeypatch.setattr(
            "setup.getpass.getpass", lambda prompt: "testpassword"
        )
        monkeypatch.setattr("builtins.input", lambda prompt: "")

        assistant.create_secrets_file()
        mode = os.stat(assistant.secrets_file).st_mode & 0o777
        assert mode == 0o600

    def test_stores_valid_password_hash(self, assistant, monkeypatch):
        monkeypatch.setattr(
            "setup.getpass.getpass", lambda prompt: "mypassword"
        )
        monkeypatch.setattr("builtins.input", lambda prompt: "")

        assistant.create_secrets_file()
        content = assistant.secrets_file.read_text()
        for line in content.splitlines():
            if line.startswith("ACCESSMAN_PASSWORD_HASH="):
                b64_value = line.split("=", 1)[1]
                raw = base64.b64decode(b64_value)
                salt = raw[:16]
                stored_dk = raw[16:]
                dk = hashlib.pbkdf2_hmac(
                    "sha256", b"mypassword", salt, 260000
                )
                assert dk == stored_dk
                return
        pytest.fail("ACCESSMAN_PASSWORD_HASH not found in .secrets")


class TestValidateSetup:
    def test_passes_with_valid_secrets(self, assistant):
        assistant.secrets_file.write_text(
            "STORAGE_SECRET=abc123\n"
            "ACCESSMAN_PASSWORD_HASH=def456\n"
        )
        results = assistant.validate_setup()
        assert results["secrets_exists"] is True
        assert results["secrets_valid"] is True
        assert results["all_ok"] is True

    def test_fails_without_secrets(self, assistant):
        results = assistant.validate_setup()
        assert results["secrets_exists"] is False
        assert results["secrets_valid"] is False
        assert results["all_ok"] is False

    def test_fails_with_missing_required_key(self, assistant):
        assistant.secrets_file.write_text("STORAGE_SECRET=abc123\n")
        results = assistant.validate_setup()
        assert results["secrets_valid"] is False


class TestSetupToolsConfig:
    def test_copies_example_to_tools_ini(self, assistant, monkeypatch):
        assistant.tools_example.write_text(
            "[tools]\nace = /usr/bin/ace\n\n[paths]\nextra =\n"
        )
        monkeypatch.setattr(assistant, "ask_yes_no", lambda q, default=True: False)
        result = assistant.setup_tools_config()
        assert result is True
        assert assistant.tools_file.exists()
        content = assistant.tools_file.read_text()
        assert "ace = /usr/bin/ace" in content


class TestDetectOS:
    def test_returns_valid_os_name(self, assistant):
        result = assistant.detect_os()
        assert result in ("Windows", "macOS", "Linux")
