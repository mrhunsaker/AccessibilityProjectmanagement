"""Accessibility Project Manager package.

Changes applied (see fix_specs.json):
  FIX-005  Removed 'models' entry from legacy import aliases and the
           SQLAlchemy-specific except branch.  The SQLAlchemy ORM layer
           (database.py, models/, and dependent services) has been deleted;
           the alias is no longer needed and the fallback branch was masking
           import errors for modules that no longer exist.
"""

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
        "db":       "accessibility_mgr.db",
        "services": "accessibility_mgr.services",
        "ui":       "accessibility_mgr.ui",
    }
    for alias, target in aliases.items():
        if alias not in sys.modules:
            mod = import_module(target)
            sys.modules[alias] = mod


_install_legacy_import_aliases()
