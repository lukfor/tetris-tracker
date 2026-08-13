from __future__ import annotations

from dataclasses import dataclass
from importlib.metadata import entry_points
from typing import Any


ENTRY_POINT_GROUP = "tetris_tracker.collectors"


@dataclass
class CollectorConfig:
    host: str
    port: int
    poll_interval: float
    options: dict[str, Any]


def discover_collectors() -> dict[str, type]:
    # Built-ins are always available, even when running directly from source.
    from tetris_tracker.collectors.nes_retroarch import NesRetroArchCollector

    found: dict[str, type] = {
        "nes-retroarch": NesRetroArchCollector,
    }

    # Third-party collectors are discovered through Python entry points.
    eps = entry_points()
    selected = eps.select(group=ENTRY_POINT_GROUP)

    for ep in selected:
        found[ep.name] = ep.load()

    return found
