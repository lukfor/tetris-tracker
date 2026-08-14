from __future__ import annotations

from typing import List, Optional

from tetris_tracker.models import GameState
from tetris_tracker.plugin import CollectorConfig
from tetris_tracker.retroarch import RetroArchClient


RAM_BLOCK_START = 0x0042
RAM_BLOCK_END = 0x0056
RAM_BLOCK_LEN = RAM_BLOCK_END - RAM_BLOCK_START + 1

ADDR_CURRENT_PIECE = 0x0042
ADDR_LEVEL = 0x0044
ADDR_PHASE = 0x0048
ADDR_LINES = 0x0050
ADDR_SCORE = 0x0053
ADDR_CLEAR_COUNT = 0x0056
ADDR_NEXT_PIECE = 0x00BF

# Phases observed during actual gameplay / animations.
# Top-out/game-over persists at phase 10 in our tests.
GAMEPLAY_PHASES = {1, 2, 3, 4, 5, 6, 7, 8}
TOP_OUT_PHASE = 10


def _bcd_byte(value: int) -> int:
    return ((value >> 4) * 10) + (value & 0x0F)


def _decode_bcd_le(values: List[int]) -> int:
    result = 0
    multiplier = 1

    for value in values:
        result += _bcd_byte(value) * multiplier
        multiplier *= 100

    return result


def _offset(address: int) -> int:
    return address - RAM_BLOCK_START


class NesRetroArchCollector:
    name = "nes-retroarch"

    def __init__(self, config: CollectorConfig):
        self.client = RetroArchClient(
            config.host,
            config.port,
            timeout=float(config.options.get("timeout", 1.0)),
        )

    def read_state(self) -> Optional[GameState]:
        try:
            block = self.client.read_memory(
                RAM_BLOCK_START,
                RAM_BLOCK_LEN,
            )
            next_piece = self.client.read_memory(
                ADDR_NEXT_PIECE,
                1,
            )[0]

        except (ConnectionError, RuntimeError):
            return None

        current_piece = block[_offset(ADDR_CURRENT_PIECE)]
        level = block[_offset(ADDR_LEVEL)]
        phase = block[_offset(ADDR_PHASE)]

        lines_start = _offset(ADDR_LINES)
        lines = _decode_bcd_le(
            block[lines_start:lines_start + 2]
        )

        score_start = _offset(ADDR_SCORE)
        score = _decode_bcd_le(
            block[score_start:score_start + 3]
        )

        clear_count = block[_offset(ADDR_CLEAR_COUNT)]

        # For the normalized state, "playing" means the sample currently
        # looks like actual gameplay. The tracker decides separately when
        # to START and when to END a run.
        playing = (
            phase in GAMEPLAY_PHASES
            and 0 <= level <= 29
        )

        return GameState(
            platform="nes",
            game="tetris",
            version="pal",
            source="retroarch",
            score=score,
            lines=lines,
            level=level,
            playing=playing,
            phase=phase,
            clear_count=clear_count,
            current_piece=current_piece,
            next_piece=next_piece,
        )

    def is_top_out(self, state: GameState) -> bool:
        return state.phase == TOP_OUT_PHASE

    def notify(self, message: str) -> None:
        try:
            self.client.show_message(message)
        except Exception:
            pass
