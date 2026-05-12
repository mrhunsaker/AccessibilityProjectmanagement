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
			except ModuleNotFoundError as exc:
				# The SQLAlchemy-backed legacy model package is optional in the
				# current SQLite-first workflow. Skip aliasing it if the dependency
				# is unavailable so the rest of the app can still start.
				if alias == "models" and exc.name == "sqlalchemy":
					continue
				raise


_install_legacy_import_aliases()
