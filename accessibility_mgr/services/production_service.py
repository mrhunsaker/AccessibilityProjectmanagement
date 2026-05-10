from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta


@dataclass
class ProductionDevice:
    name: str
    device_type: str
    status: str = "available"
    material: str = ""
    last_maintenance: str = ""
    next_maintenance: str = ""


class ProductionService:
    devices: list[ProductionDevice] = []

    @classmethod
    def register_device(cls, name: str, device_type: str, material: str = ""):
        today = datetime.utcnow()
        device = ProductionDevice(
            name=name,
            device_type=device_type,
            material=material,
            last_maintenance=today.isoformat(),
            next_maintenance=(today + timedelta(days=30)).isoformat(),
        )
        cls.devices.append(device)
        return device

    @classmethod
    def list_devices(cls):
        return cls.devices
