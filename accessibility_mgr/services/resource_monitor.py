"""System resource monitoring service.

STUB-033: Replaces a previous stub that returned hardcoded placeholder values.
This implementation uses ``psutil`` when available and falls back to stdlib
``shutil`` / ``os`` primitives so the app remains functional without psutil.

Metrics surfaced:
- CPU usage percent (1-second sample)
- Memory: total, available, used percent
- Disk: total, free, used percent for the database directory
- Process: current-process RSS memory
"""

from __future__ import annotations

import logging
import os
import shutil
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)


@dataclass
class SystemSnapshot:
    """Point-in-time system resource snapshot."""
    sampled_at: str
    cpu_percent: float | None
    memory_total_mb: float | None
    memory_available_mb: float | None
    memory_used_percent: float | None
    disk_total_gb: float | None
    disk_free_gb: float | None
    disk_used_percent: float | None
    process_rss_mb: float | None
    source: str  # "psutil" | "stdlib"


def _try_psutil(data_dir: Path) -> SystemSnapshot | None:
    """Attempt to collect metrics via psutil; return None if not installed."""
    try:
        import psutil  # type: ignore[import]
        import os as _os

        cpu   = psutil.cpu_percent(interval=1)
        mem   = psutil.virtual_memory()
        disk  = psutil.disk_usage(str(data_dir))
        proc  = psutil.Process(_os.getpid()).memory_info().rss / 1_048_576

        return SystemSnapshot(
            sampled_at=datetime.now(timezone.utc).isoformat(),
            cpu_percent=round(cpu, 1),
            memory_total_mb=round(mem.total / 1_048_576, 1),
            memory_available_mb=round(mem.available / 1_048_576, 1),
            memory_used_percent=round(mem.percent, 1),
            disk_total_gb=round(disk.total / 1_073_741_824, 2),
            disk_free_gb=round(disk.free / 1_073_741_824, 2),
            disk_used_percent=round(disk.percent, 1),
            process_rss_mb=round(proc, 1),
            source="psutil",
        )
    except ImportError:
        return None
    except Exception as exc:  # noqa: BLE001
        log.debug("psutil metric collection failed: %s", exc)
        return None


def _stdlib_snapshot(data_dir: Path) -> SystemSnapshot:
    """Collect a reduced set of metrics using stdlib only."""
    disk  = shutil.disk_usage(str(data_dir))
    total = disk.total or 1
    used  = disk.used

    # RSS via /proc/self/status on Linux; None elsewhere
    rss: float | None = None
    try:
        status = Path("/proc/self/status").read_text()
        for line in status.splitlines():
            if line.startswith("VmRSS:"):
                rss = round(int(line.split()[1]) / 1024, 1)
                break
    except OSError:
        pass

    return SystemSnapshot(
        sampled_at=datetime.now(timezone.utc).isoformat(),
        cpu_percent=None,
        memory_total_mb=None,
        memory_available_mb=None,
        memory_used_percent=None,
        disk_total_gb=round(disk.total / 1_073_741_824, 2),
        disk_free_gb=round(disk.free / 1_073_741_824, 2),
        disk_used_percent=round(used / total * 100, 1),
        process_rss_mb=rss,
        source="stdlib",
    )


class ResourceMonitorService:
    """Collect and expose system resource metrics.

    STUB-033: all methods now return real OS-level data, not hardcoded stubs.
    psutil is used when available; stdlib fallback is used otherwise.
    """

    def __init__(self) -> None:
        self._history: list[SystemSnapshot] = []
        self._data_dir: Path = self._resolve_data_dir()

    @staticmethod
    def _resolve_data_dir() -> Path:
        try:
            from ..db.schema import DATA_DIR
            return DATA_DIR
        except Exception:
            return Path.cwd()

    def snapshot(self) -> SystemSnapshot:
        """Take a real-time system snapshot and append it to internal history."""
        snap = _try_psutil(self._data_dir) or _stdlib_snapshot(self._data_dir)
        self._history.append(snap)
        return snap

    def current(self) -> dict[str, Any]:
        """Return the most recent snapshot as a dict (taking a new one if needed)."""
        if not self._history:
            return asdict(self.snapshot())
        return asdict(self._history[-1])

    def history(self, limit: int = 60) -> list[dict[str, Any]]:
        """Return the last *limit* snapshots."""
        return [asdict(s) for s in self._history[-limit:]]

    def disk_warning(self, threshold_gb: float = 1.0) -> str | None:
        """Return a warning string if free disk space is below *threshold_gb*, else None."""
        snap = _try_psutil(self._data_dir) or _stdlib_snapshot(self._data_dir)
        if snap.disk_free_gb is not None and snap.disk_free_gb < threshold_gb:
            return (
                f"Low disk space: {snap.disk_free_gb:.2f} GB free "
                f"(threshold {threshold_gb:.1f} GB) in {self._data_dir}"
            )
        return None


__all__ = ["ResourceMonitorService", "SystemSnapshot"]
