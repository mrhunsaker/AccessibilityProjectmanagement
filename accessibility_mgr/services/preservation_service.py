from __future__ import annotations

import hashlib
from pathlib import Path


class PreservationService:
    @staticmethod
    def generate_checksum(path: str) -> str:
        file_path = Path(path)

        if not file_path.exists():
            return "missing"

        sha256 = hashlib.sha256()

        with open(file_path, "rb") as handle:
            while chunk := handle.read(8192):
                sha256.update(chunk)

        return sha256.hexdigest()

    @staticmethod
    def build_premis_event(event_type: str, outcome: str):
        return {
            "event_type": event_type,
            "outcome": outcome,
        }
