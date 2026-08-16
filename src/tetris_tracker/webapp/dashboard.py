import html

from tetris_tracker.webapp.data import Data
from tetris_tracker.webapp.formatting import (
    fmt_date,
    fmt_duration,
    fmt_score,
    score_per_line,
    tetris_rate,
)
from tetris_tracker.webapp.layout import page


def rows_html(rows, ranked):
    if not rows:
        return """
        <tr>
            <td colspan="12" class="empty">
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
        spl = score_per_line(
            row["final_score"],
            row["final_lines"],
        )

        status = row["validation_status"]

        if status == "valid":
            status_html = '<span class="valid">✓ OK</span>'
        elif status == "warning":
            error = html.escape(
                row["validation_error"]
                or "Validation warning"
            )
            status_html = (
                '<span class="warning" title="{}">'
                '⚠ CHECK'
                '</span>'
            ).format(error)
        else:
            status_html = '<span class="unknown">—</span>'

        score_html = (
            '<a class="score-link" href="/run/{run_id}">'
            '{score}'
            '</a>'
        ).format(
            run_id=row["id"],
            score=fmt_score(row["final_score"]),
        )

        version = html.escape(
            str(row["version"] or "—").upper()
        )

        result.append(
            """
            <tr>
                <td class="rank">{rank}</td>
                <td class="score">{score}</td>
                <td>{spl:,.0f}</td>
                <td>{start_level}</td>
                <td>{end_level}</td>
                <td>{lines}</td>
                <td>{tetrises}</td>
                <td>{rate:.1f}%</td>
                <td>{duration}</td>
                <td>{date}</td>
                <td>{version}</td>
                <td>{status}</td>
            </tr>
            """.format(
                rank=rank,
                score=score_html,
                version=version,
                spl=spl,
                start_level=row["start_level"],
                end_level=row["end_level"],
                lines=row["final_lines"],
                tetrises=row["tetrises"],
                rate=rate,
                duration=fmt_duration(row["game_seconds"]),
                date=html.escape(fmt_date(row["ended_at"])),
                status=status_html,
            )
        )

    return "".join(result)


def render_table(rows, ranked):
    return """
    <div class="table-wrap">
        <table>
            <thead>
                <tr>
                    <th>#</th>
                    <th>Score</th>
                    <th>Score / Line</th>
                    <th>Start Lv</th>
                    <th>End Lv</th>
                    <th>Lines</th>
                    <th>Tetrises</th>
                    <th>Tetris %</th>
                    <th>Game Time</th>
                    <th>Date</th>
                    <th>Version</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>
    </div>
    """.format(rows=rows_html(rows, ranked))


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

    body = """
    <div class="cards">
        <div class="card">
            <div class="label">Highscore</div>
            <div class="value">{highscore}</div>
        </div>

        <div class="card">
            <div class="label">Games</div>
            <div class="value">{games}</div>
        </div>

        <div class="card">
            <div class="label">Lines</div>
            <div class="value">{lines}</div>
        </div>

        <div class="card">
            <div class="label">Tetris Rate</div>
            <div class="value">{rate:.1f}%</div>
        </div>
    </div>

    <section>
        <h2>Highscores</h2>
        {highscores}
    </section>

    <section>
        <h2>Latest Games</h2>
        {latest}
    </section>

    <footer>
        Data is read directly from the local SQLite database.
    </footer>
    """.format(
        highscore=fmt_score(summary["highscore"]),
        games=summary["games"],
        lines=fmt_score(total_lines),
        rate=overall_rate,
        highscores=render_table(highscores, True),
        latest=render_table(latest, False),
    )

    return page(
        "Tetris Tracker",
        body,
        current_player=current_player,
        refresh=True,
    )