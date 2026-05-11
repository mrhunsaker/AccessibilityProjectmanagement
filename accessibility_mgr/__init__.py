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
		"models": "accessibility_mgr.models",
		"services": "accessibility_mgr.services",
		"ui": "accessibility_mgr.ui",
	}
	for alias, target in aliases.items():
		if alias not in sys.modules:
			sys.modules[alias] = import_module(target)


_install_legacy_import_aliases()
