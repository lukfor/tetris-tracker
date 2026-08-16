from __future__ import annotations

import re
import time
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

GAMEPLAY_PHASES = {1, 2, 3, 4, 5, 6, 7, 8}
TOP_OUT_PHASE = 10


# CRC32 -> normalized version name.
#
# Replace these with the CRCs of the ROMs you actually want to support.
KNOWN_TETRIS_ROMS = {
    "C99B0FCA": "pal",
    "D16EA396": "ntsc",
    "6D72C53A": "ntsc"
}

# GET_STATUS is much less time-critical than RAM polling.
STATUS_POLL_INTERVAL = 2.0

_STATUS_RE = re.compile(
    r"^GET_STATUS\s+(PLAYING|PAUSED)\s+([^,]+),(.+),crc32=([0-9A-Fa-f]{8})$"
)


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

        self.status_poll_interval = float(
            config.options.get(
                "status_poll_interval",
                STATUS_POLL_INTERVAL,
            )
        )

        self._last_status_check = 0.0
        self._version: Optional[str] = None
        self._crc32: Optional[str] = None
        self._last_reported_crc32: Optional[str] = None

    def _refresh_content_status(self) -> None:
        now = time.monotonic()

        if (
            self._last_status_check
            and now - self._last_status_check < self.status_poll_interval
        ):
            return

        self._last_status_check = now

        try:
            status = self.client.get_status()
        except (ConnectionError, RuntimeError):
            self._version = None
            self._crc32 = None
            return

        match = _STATUS_RE.match(status.strip())

        if not match:
            # CONTENTLESS or unexpected response.
            self._version = None
            self._crc32 = None
            return

        state, system_id, game_name, crc32 = match.groups()

        crc32 = crc32.upper()

        self._crc32 = crc32
        self._version = KNOWN_TETRIS_ROMS.get(crc32)

        # Nur melden, wenn tatsächlich ein anderes Spiel / ROM erkannt wurde.
        if crc32 != self._last_reported_crc32:
            self._last_reported_crc32 = crc32

            if self._version is not None:
                message = (
                    f"Neues Spiel mit CRC32 {crc32} eingelegt. "
                    f"Version {self._version} erkannt."
                )
            else:
                message = (
                    f"Neues Spiel mit CRC32 {crc32} eingelegt. "
                    f"Keine unterstützte Tetris-Variante."
                )

            print(f"[rom] {message}")
            self.notify(message)

    def read_state(self) -> Optional[GameState]:
        # Cheap / infrequent content identification first.
        self._refresh_content_status()

        # Unknown ROM, no content, wrong system, RetroArch unavailable, etc.
        # => DO NOT touch emulator memory.
        if self._version is None:
            return None

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

        playing = (
            phase in GAMEPLAY_PHASES
            and 0 <= level <= 29
        )

        return GameState(
            platform="nes",
            game="tetris",
            version=self._version,
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