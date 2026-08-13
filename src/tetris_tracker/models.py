from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class GameState:
    platform: str
    game: str
    version: str
    source: str

    score: int
    lines: int
    level: int
    playing: bool

    phase: Optional[int] = None
    clear_count: int = 0
    current_piece: Optional[int] = None
    next_piece: Optional[int] = None
    board: Optional[bytes] = None
