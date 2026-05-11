"""
Tools service — resolves external tool executables and augments PATH.

On import this module does nothing.  Call ``bootstrap()`` (or ``init()``)
once at application startup to:

1. Read ``tools.ini`` from the project root.
2. Prepend any ``[paths] extra`` directories to ``os.environ["PATH"]``.
3. Resolve each tool's executable via the config, then ``shutil.which()``.
4. Cache resolved paths so the rest of the app can call ``resolve(name)``
   without re-scanning.

Tool names recognised:
  - "ace"       → DAISY Ace
  - "epubcheck" → EPUBCheck
  - "pipeline"  → DAISY Pipeline
  - "liblouis"  → LibLouis CLI (lou_translate / file2brl / etc.)
"""

from __future__ import annotations

import configparser
import logging
import os
import shutil
from pathlib import Path

log = logging.getLogger(__name__)

# ── Defaults used when tools.ini is absent or a key is missing ───────────────
_DEFAULTS: dict[str, str] = {
    "ace": "ace",
    "epubcheck": "epubcheck",
    "pipeline": "pipeline2",
    "liblouis": "lou_translate",
}

# Resolved absolute paths (or None if not found), populated by bootstrap().
_resolved: dict[str, str | None] = {}

_bootstrapped: bool = False


def _config_path() -> Path:
    """Return the absolute path to tools.ini (project root)."""
    # This file lives at:  <project>/accessibility_mgr/services/tools_service.py
    # tools.ini lives at:  <project>/tools.ini
    return Path(__file__).parent.parent.parent / "tools.ini"


def bootstrap() -> None:
    """Read tools.ini, extend PATH, and cache resolved tool paths.

    Safe to call multiple times — subsequent calls are no-ops.
    """
    global _bootstrapped
    if _bootstrapped:
        return

    cfg = configparser.ConfigParser(default_section="DEFAULT")
    ini = _config_path()

    if ini.exists():
        cfg.read(ini)
        log.debug("tools_service: loaded %s", ini)
    else:
        log.warning(
            "tools_service: %s not found; using default tool names. "
            "Copy tools.ini.example or create tools.ini to customise.",
            ini,
        )

    # ── 1. Extend PATH with extra directories ─────────────────────────────
    raw_extra = cfg.get("paths", "extra", fallback="").strip()
    if raw_extra:
        extra_dirs = [d.strip() for d in raw_extra.splitlines() if d.strip()]
        if extra_dirs:
            current_path = os.environ.get("PATH", "")
            prepend = os.pathsep.join(extra_dirs)
            os.environ["PATH"] = prepend + os.pathsep + current_path
            log.info("tools_service: prepended to PATH: %s", prepend)

    # ── 2. Resolve each tool ───────────────────────────────────────────────
    for key, default_name in _DEFAULTS.items():
        configured = cfg.get("tools", key, fallback=default_name).strip()

        # If the user supplied an absolute path, use it directly.
        if os.path.isabs(configured):
            if os.path.isfile(configured) and os.access(configured, os.X_OK):
                _resolved[key] = configured
                log.info("tools_service: %s → %s (absolute path)", key, configured)
            else:
                _resolved[key] = None
                log.warning(
                    "tools_service: %s configured as '%s' but file not found or not executable.",
                    key,
                    configured,
                )
        else:
            # Bare name — search updated PATH.
            found = shutil.which(configured)
            if found:
                _resolved[key] = found
                log.info("tools_service: %s → %s", key, found)
            else:
                _resolved[key] = None
                log.warning(
                    "tools_service: '%s' (%s) not found on PATH. "
                    "Install the tool or set its path in tools.ini.",
                    configured,
                    key,
                )

    _bootstrapped = True


# Alias so callers can write ``tools_service.init()`` if they prefer.
init = bootstrap


def resolve(tool: str) -> str | None:
    """Return the resolved absolute path for *tool*, or None if not found.

    Calls ``bootstrap()`` automatically on first use.

    Example::

        ace_bin = tools_service.resolve("ace")
        if ace_bin is None:
            raise RuntimeError("DAISY Ace is not installed")
        subprocess.run([ace_bin, "book.epub", "-o", "report"])
    """
    if not _bootstrapped:
        bootstrap()
    return _resolved.get(tool)


def status() -> dict[str, str | None]:
    """Return a copy of the resolved-tool map (useful for the Admin UI)."""
    if not _bootstrapped:
        bootstrap()
    return dict(_resolved)
