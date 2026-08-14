from __future__ import annotations

from dataclasses import dataclass
try:
    from importlib.metadata import entry_points
except Exception:
    # importlib.metadata is only in stdlib from Python 3.8+; use backport on 3.7
    from importlib_metadata import entry_points

from typing import Any, Dict, Type


ENTRY_POINT_GROUP = "tetris_tracker.collectors"


@dataclass
class CollectorConfig:
    host: str
    port: int
    poll_interval: float
    options: Dict[str, Any]


def discover_collectors() -> Dict[str, Type]:
    # Built-ins are always available, even when running directly from source.
    from tetris_tracker.collectors.nes_retroarch import NesRetroArchCollector

    found: Dict[str, Type] = {
        "nes-retroarch": NesRetroArchCollector,
    }

    # Third-party collectors are discovered through Python entry points.
    eps = entry_points()
    # entry_points() shape differs between versions; support older backport and newer stdlib
    if hasattr(eps, "select"):
        selected = eps.select(group=ENTRY_POINT_GROUP)
    else:
        try:
            selected = entry_points(group=ENTRY_POINT_GROUP)
        except TypeError:
            # Fallback: filter generic sequence
            selected = [ep for ep in eps if getattr(ep, "group", None) == ENTRY_POINT_GROUP]

    for ep in selected:
        found[ep.name] = ep.load()

    return found
