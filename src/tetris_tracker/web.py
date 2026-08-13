from __future__ import annotations

import argparse
import html
import sqlite3
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


def fmt_score(value):
    return "-" if value is None else f"{value:,}"


def fmt_duration(seconds):
    if seconds is None:
        return "-"

    seconds = max(0, int(seconds))
    hours, rem = divmod(seconds, 3600)
    minutes, secs = divmod(rem, 60)

    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"

    return f"{minutes}:{secs:02d}"


def fmt_date(value):
    if not value:
        return "-"

    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M")
    except ValueError:
        return value


def tetris_rate(tetrises, lines):
    if not lines:
        return 0.0

    return (int(tetrises or 0) * 4.0 / int(lines)) * 100.0


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
    r.started_at,
    r.ended_at,
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


def rows_html(rows, ranked):
    if not rows:
        return """
        <tr>
            <td colspan="9" class="empty">
                No completed games yet.
            </td>
        </tr>
        """

    result = []

    for index, row in enumerate(rows, 1):
        rank = index if ranked else "—"
        rate = tetris_rate(
            row["tetrises"],
            row["final_lines"],
        )

        result.append(
            f"""
            <tr>
                <td class="rank">{rank}</td>
                <td class="score">{fmt_score(row["final_score"])}</td>
                <td>{row["start_level"]}</td>
                <td>{row["end_level"]}</td>
                <td>{row["final_lines"]}</td>
                <td>{row["tetrises"]}</td>
                <td>{rate:.1f}%</td>
                <td>{fmt_duration(row["game_seconds"])}</td>
                <td>{html.escape(fmt_date(row["ended_at"]))}</td>
            </tr>
            """
        )

    return "".join(result)


def render_table(rows, ranked):
    return f"""
    <div class="table-wrap">
        <table>
            <thead>
                <tr>
                    <th>#</th>
                    <th>Score</th>
                    <th>Start Lv</th>
                    <th>End Lv</th>
                    <th>Lines</th>
                    <th>Tetrises</th>
                    <th>Tetris %</th>
                    <th>Game Time</th>
                    <th>Date</th>
                </tr>
            </thead>
            <tbody>
                {rows_html(rows, ranked)}
            </tbody>
        </table>
    </div>
    """


def render(db):
    data = Data(db)

    highscores = data.highscores()
    latest = data.latest()
    summary = data.summary()
    current_player = data.current_player()

    total_lines = int(summary["lines"] or 0)
    total_tetrises = int(summary["tetrises"] or 0)

    overall_rate = tetris_rate(
        total_tetrises,
        total_lines,
    )

    return f"""<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta
        name="viewport"
        content="width=device-width, initial-scale=1"
    >
    <meta http-equiv="refresh" content="15">

    <title>Tetris Tracker</title>

    <style>
        :root {{
            color-scheme: dark;

            /* Nord - Polar Night */
            --nord0: #2e3440;
            --nord1: #3b4252;
            --nord2: #434c5e;
            --nord3: #4c566a;

            /* Nord - Snow Storm */
            --nord4: #d8dee9;
            --nord5: #e5e9f0;
            --nord6: #eceff4;

            /* Nord - Frost */
            --nord7: #8fbcbb;
            --nord8: #88c0d0;
            --nord9: #81a1c1;
            --nord10: #5e81ac;

            /* Nord - Aurora */
            --nord11: #bf616a;
            --nord12: #d08770;
            --nord13: #ebcb8b;
            --nord14: #a3be8c;
            --nord15: #b48ead;

            --bg: var(--nord0);
            --panel: var(--nord1);
            --panel-2: var(--nord2);
            --border: var(--nord3);
            --text: var(--nord6);
            --muted: var(--nord4);
            --accent: var(--nord8);
            --score: var(--nord13);
        }}

        * {{
            box-sizing: border-box;
        }}

        body {{
            margin: 0;
            background: var(--bg);
            color: var(--text);
            font-family:
                -apple-system,
                BlinkMacSystemFont,
                "Segoe UI",
                sans-serif;
        }}

        main {{
            width: min(1180px, calc(100% - 32px));
            margin: 0 auto;
            padding: 34px 0 60px;
        }}

        header {{
            display: flex;
            align-items: end;
            justify-content: space-between;
            gap: 24px;
            margin-bottom: 24px;
        }}

        h1 {{
            margin: 0;
            font-size: clamp(30px, 4vw, 44px);
            letter-spacing: -0.045em;
        }}

        h2 {{
            margin: 0 0 12px;
            font-size: 20px;
        }}

        .subtitle,
        .muted {{
            color: var(--muted);
        }}

        .subtitle {{
            margin-top: 6px;
        }}

        .refresh {{
            font-size: 13px;
        }}

        .header-meta {{
            display: flex;
            align-items: center;
            gap: 12px;
        }}

        .player-chip {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 8px 11px;
            background: var(--panel);
            border: 1px solid var(--border);
            border-radius: 999px;
            color: var(--text);
            font-size: 13px;
            font-weight: 650;
        }}

        .player-dot {{
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--nord14);
            box-shadow: 0 0 0 3px rgba(163, 190, 140, 0.12);
        }}

        .cards {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 14px;
            margin: 24px 0 30px;
        }}

        .card {{
            background: var(--panel);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 18px;
            box-shadow:
                0 1px 2px rgba(0, 0, 0, 0.12);
        }}

        .label {{
            color: var(--muted);
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.08em;
        }}

        .value {{
            margin-top: 7px;
            font-size: 28px;
            font-weight: 760;
            letter-spacing: -0.02em;
        }}

        .card:first-child .value {{
            color: var(--accent);
        }}

        section {{
            margin-top: 28px;
        }}

        .table-wrap {{
            overflow-x: auto;
            background: var(--panel);
            border: 1px solid var(--border);
            border-radius: 14px;
            box-shadow:
                0 1px 2px rgba(0, 0, 0, 0.12);
        }}

        table {{
            width: 100%;
            min-width: 850px;
            border-collapse: collapse;
        }}

        th {{
            padding: 12px 14px;
            text-align: left;
            background: var(--panel-2);
            color: var(--muted);
            font-size: 11px;
            font-weight: 650;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            border-bottom: 1px solid var(--border);
        }}

        td {{
            padding: 12px 14px;
            border-bottom: 1px solid var(--border);
            font-variant-numeric: tabular-nums;
        }}

        tbody tr:last-child td {{
            border-bottom: none;
        }}

        tbody tr {{
            transition: background 100ms ease;
        }}

        tbody tr:hover {{
            background: rgba(136, 192, 208, 0.07);
        }}

        .rank {{
            width: 42px;
            color: var(--muted);
        }}

        .score {{
            color: var(--score);
            font-weight: 750;
        }}

        .empty {{
            padding: 30px;
            text-align: center;
            color: var(--muted);
        }}

        footer {{
            margin-top: 28px;
            color: var(--muted);
            font-size: 12px;
        }}

        @media (max-width: 760px) {{
            header {{
                display: block;
            }}

            .header-meta {{
                margin-top: 12px;
                justify-content: space-between;
            }}

            .refresh {{
                margin-top: 0;
            }}

            .cards {{
                grid-template-columns: repeat(2, 1fr);
            }}
        }}
    </style>
</head>

<body>
    <main>
        <header>
            <div>
                <h1>Tetris Tracker</h1>
                <div class="subtitle">
                    NES Tetris training log
                </div>
            </div>

            <div class="header-meta">
                <div class="player-chip">
                    <span class="player-dot"></span>
                    <span>{html.escape(current_player)}</span>
                </div>
                <div class="refresh muted">
                    Refreshes every 15 seconds
                </div>
            </div>
        </header>

        <div class="cards">
            <div class="card">
                <div class="label">Highscore</div>
                <div class="value">
                    {fmt_score(summary["highscore"])}
                </div>
            </div>

            <div class="card">
                <div class="label">Games</div>
                <div class="value">
                    {summary["games"]}
                </div>
            </div>

            <div class="card">
                <div class="label">Lines</div>
                <div class="value">
                    {fmt_score(total_lines)}
                </div>
            </div>

            <div class="card">
                <div class="label">Tetris Rate</div>
                <div class="value">
                    {overall_rate:.1f}%
                </div>
            </div>
        </div>

        <section>
            <h2>Highscores</h2>
            {render_table(highscores, True)}
        </section>

        <section>
            <h2>Latest Games</h2>
            {render_table(latest, False)}
        </section>

        <footer>
            Data is read directly from the local SQLite database.
        </footer>
    </main>
</body>
</html>
"""


def serve(db, host, port):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path not in ("/", "/index.html"):
                self.send_error(404)
                return

            try:
                body = render(db).encode("utf-8")
                self.send_response(200)
            except sqlite3.Error as exc:
                body = (
                    "<h1>Database error</h1>"
                    f"<pre>{html.escape(str(exc))}</pre>"
                ).encode("utf-8")
                self.send_response(500)

            self.send_header(
                "Content-Type",
                "text/html; charset=utf-8",
            )
            self.send_header(
                "Cache-Control",
                "no-store",
            )
            self.send_header(
                "Content-Length",
                str(len(body)),
            )
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format, *args):
            pass

    server = ThreadingHTTPServer(
        (host, port),
        Handler,
    )

    print(
        f"Tetris Tracker web: "
        f"http://{host}:{port} "
        f"db={db}",
        flush=True,
    )

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def main():
    parser = argparse.ArgumentParser(
        prog="tetris-tracker-web"
    )

    parser.add_argument(
        "--db",
        default="./tetris.db",
    )

    parser.add_argument(
        "--host",
        default="127.0.0.1",
    )

    parser.add_argument(
        "--port",
        type=int,
        default=8001,
    )

    args = parser.parse_args()

    serve(
        args.db,
        args.host,
        args.port,
    )


if __name__ == "__main__":
    main()