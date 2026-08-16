import sqlite3
from pathlib import Path


RUN_SQL = """
SELECT
    r.id,
    r.run_uuid,
    p.name AS player,
    r.final_score,
    r.start_level,
    r.end_level,
    r.final_lines,
    r.tetrises,
    r.validation_status,
    r.validation_error,
    r.started_at,
    r.ended_at,
    r.version,    
    CAST(
        ROUND(
            (julianday(r.ended_at) - julianday(r.started_at))
            * 86400.0
        ) AS INTEGER
    ) AS game_seconds
FROM runs r
JOIN players p ON p.id = r.player_id
WHERE r.status = 'completed'
  AND r.final_score IS NOT NULL
"""


class Data:
    def __init__(self, db):
        self.db = str(Path(db).expanduser())

    def query(self, sql, params=()):
        with sqlite3.connect(self.db) as conn:
            conn.row_factory = sqlite3.Row
            return conn.execute(sql, params).fetchall()

    def highscores(self):
        return self.query(
            RUN_SQL
            + """
            ORDER BY r.final_score DESC, r.ended_at ASC
            LIMIT 10
            """
        )

    def latest(self):
        return self.query(
            RUN_SQL
            + """
            ORDER BY r.ended_at DESC
            LIMIT 30
            """
        )

    def summary(self):
        return self.query(
            """
            SELECT
                COUNT(*) AS games,
                MAX(final_score) AS highscore,
                COALESCE(SUM(final_lines), 0) AS lines,
                COALESCE(SUM(tetrises), 0) AS tetrises
            FROM runs
            WHERE status = 'completed'
            """
        )[0]

    def current_player(self):
        rows = self.query(
            """
            SELECT p.name
            FROM players p
            JOIN runs r ON r.player_id = p.id
            ORDER BY r.id DESC
            LIMIT 1
            """
        )
        return rows[0]["name"] if rows else "Player"

    def run(self, run_id):
        rows = self.query(
            RUN_SQL
            + """
            AND r.id = ?
            LIMIT 1
            """,
            (run_id,),
        )
        return rows[0] if rows else None

    def run_events(self, run_id):
        return self.query(
            """
            SELECT
                id,
                run_id,
                occurred_at,
                type,
                score,
                lines,
                level,
                value,
                payload_json
            FROM events
            WHERE run_id = ?
            ORDER BY occurred_at ASC, id ASC
            """,
            (run_id,),
        )
