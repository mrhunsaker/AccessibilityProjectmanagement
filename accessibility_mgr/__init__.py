"""Accessibility Project Manager package."""

from __future__ import annotations

import sys
from importlib import import_module


def _install_legacy_import_aliases() -> None:
    """Support legacy absolute imports used throughout the codebase.

    Several modules still import siblings as top-level packages (e.g. ``db.schema``)
    even though this project is distributed as ``accessibility_mgr``. Creating module
    aliases keeps those imports working when launched via the installed script.
    """

    aliases = {
        "db": "accessibility_mgr.db",
        "services": "accessibility_mgr.services",
        "ui": "accessibility_mgr.ui",
    }
    for alias, target in aliases.items():
        if alias not in sys.modules:
            try:
                sys.modules[alias] = import_module(target)
            except ImportError:
                pass  # subpackage not available (e.g. PyInstaller partial bundle)


_install_legacy_import_aliases()
