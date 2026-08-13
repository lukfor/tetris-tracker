from __future__ import annotations

import json
import sqlite3
import uuid
from pathlib import Path
from typing import Optional

from tetris_tracker.models import GameState


SCHEMA = """
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS players (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_uuid TEXT NOT NULL UNIQUE,
    player_id INTEGER NOT NULL REFERENCES players(id),

    platform TEXT NOT NULL,
    game TEXT NOT NULL,
    version TEXT NOT NULL,
    source TEXT NOT NULL,

    started_at TEXT NOT NULL,
    ended_at TEXT,

    start_level INTEGER NOT NULL,
    end_level INTEGER,
    final_score INTEGER,
    final_lines INTEGER,

    singles INTEGER NOT NULL DEFAULT 0,
    doubles INTEGER NOT NULL DEFAULT 0,
    triples INTEGER NOT NULL DEFAULT 0,
    tetrises INTEGER NOT NULL DEFAULT 0,

    status TEXT NOT NULL DEFAULT 'active',
    synced_at TEXT
);

CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    occurred_at TEXT NOT NULL,
    type TEXT NOT NULL,
    score INTEGER,
    lines INTEGER,
    level INTEGER,
    value INTEGER,
    payload_json TEXT
);

CREATE TABLE IF NOT EXISTS piece_states (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    piece_index INTEGER NOT NULL,
    occurred_at TEXT NOT NULL,
    current_piece INTEGER,
    next_piece INTEGER,
    score INTEGER,
    lines INTEGER,
    level INTEGER,
    board BLOB NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_piece_states_run_piece
    ON piece_states(run_id, piece_index);
CREATE INDEX IF NOT EXISTS idx_piece_states_run_id
    ON piece_states(run_id);
CREATE INDEX IF NOT EXISTS idx_events_run_id
    ON events(run_id);
CREATE INDEX IF NOT EXISTS idx_runs_started_at
    ON runs(started_at);
CREATE INDEX IF NOT EXISTS idx_runs_player_id
    ON runs(player_id);
"""


class Storage:
    DEFAULT_PLAYER_NAME = "Lukas"

    REQUIRED_RUN_COLUMNS = {
        "id",
        "player_id",
        "platform",
        "game",
        "version",
        "source",
        "started_at",
        "ended_at",
        "start_level",
        "end_level",
        "final_score",
        "final_lines",
        "singles",
        "doubles",
        "triples",
        "tetrises",
        "status",
    }


    def __init__(self, path: str):
        self.db_path = Path(path).expanduser()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute("PRAGMA foreign_keys=ON")
        self.conn.executescript(SCHEMA)

        self.default_player_id = self._ensure_default_player()
        self.conn.commit()

    def _ensure_default_player(self) -> int:
        self.conn.execute(
            "INSERT OR IGNORE INTO players (name) VALUES (?)",
            (self.DEFAULT_PLAYER_NAME,),
        )

        row = self.conn.execute(
            "SELECT id FROM players WHERE name=?",
            (self.DEFAULT_PLAYER_NAME,),
        ).fetchone()

        if row is None:
            raise RuntimeError("Could not create default player")

        return int(row[0])

    def start_run(self, state: GameState, started_at: str) -> int:
        cur = self.conn.execute(
            """
            INSERT INTO runs (
                run_uuid, player_id, platform, game, version, source,
                started_at, start_level, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active')
            """,
            (
                str(uuid.uuid4()),
                self.default_player_id,
                state.platform,
                state.game,
                state.version,
                state.source,
                started_at,
                state.level,
            ),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def add_event(
        self,
        run_id: int,
        occurred_at: str,
        event_type: str,
        state: GameState,
        value: Optional[int] = None,
        payload: Optional[dict] = None,
    ) -> None:
        self.conn.execute(
            """
            INSERT INTO events (
                run_id, occurred_at, type,
                score, lines, level, value, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                occurred_at,
                event_type,
                state.score,
                state.lines,
                state.level,
                value,
                json.dumps(payload) if payload is not None else None,
            ),
        )
        self.conn.commit()

    def add_piece_state(
        self,
        run_id: int,
        piece_index: int,
        occurred_at: str,
        state: GameState,
        board: bytes,
    ) -> None:
        self.conn.execute(
            """
            INSERT INTO piece_states (
                run_id, piece_index, occurred_at,
                current_piece, next_piece,
                score, lines, level, board
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                piece_index,
                occurred_at,
                state.current_piece,
                state.next_piece,
                state.score,
                state.lines,
                state.level,
                sqlite3.Binary(board),
            ),
        )
        self.conn.commit()

    def best_score_before_run(self, run_id: int, state: GameState) -> int | None:
        row = self.conn.execute(
            """
            SELECT MAX(final_score)
            FROM runs
            WHERE id <> ?
              AND player_id = ?
              AND platform = ?
              AND game = ?
              AND version = ?
              AND final_score IS NOT NULL
              AND status = 'completed'
            """,
            (
                run_id,
                self.default_player_id,
                state.platform,
                state.game,
                state.version,
            ),
        ).fetchone()

        return None if row is None or row[0] is None else int(row[0])

    def finish_run(
        self,
        run_id: int,
        ended_at: str,
        state: GameState,
        clears: dict[int, int],
    ) -> bool:
        previous_best = self.best_score_before_run(run_id, state)

        self.conn.execute(
            """
            UPDATE runs
            SET ended_at=?,
                end_level=?,
                final_score=?,
                final_lines=?,
                singles=?,
                doubles=?,
                triples=?,
                tetrises=?,
                status='completed'
            WHERE id=?
            """,
            (
                ended_at,
                state.level,
                state.score,
                state.lines,
                clears.get(1, 0),
                clears.get(2, 0),
                clears.get(3, 0),
                clears.get(4, 0),
                run_id,
            ),
        )
        self.conn.commit()

        return previous_best is None or state.score > previous_best

    def interrupt_run(
        self,
        run_id: int,
        ended_at: str,
        state: GameState,
    ) -> None:
        self.conn.execute(
            """
            UPDATE runs
            SET ended_at=?,
                end_level=?,
                final_score=?,
                final_lines=?,
                status='interrupted'
            WHERE id=?
            """,
            (
                ended_at,
                state.level,
                state.score,
                state.lines,
                run_id,
            ),
        )
        self.conn.commit()
