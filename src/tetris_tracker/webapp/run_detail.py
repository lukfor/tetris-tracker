import html
import json
from datetime import datetime

from tetris_tracker.webapp.data import Data
from tetris_tracker.webapp.formatting import (
    fmt_date,
    fmt_duration,
    fmt_score,
    score_per_line,
    tetris_rate,
)
from tetris_tracker.webapp.layout import page


def _parse_time(value):
    if not value:
        return None

    try:
        return datetime.fromisoformat(
            value.replace("Z", "+00:00")
        )
    except ValueError:
        return None


def _event_elapsed_seconds(started_at, occurred_at):
    start = _parse_time(started_at)
    current = _parse_time(occurred_at)

    if start is None or current is None:
        return 0.0

    return max(0.0, (current - start).total_seconds())


def _event_class(event_type):
    if event_type == "tetris":
        return "event-type event-tetris"

    if event_type == "level_change":
        return "event-type event-level"

    return "event-type"


def _events_html(run, events):
    if not events:
        return """
        <tr>
            <td colspan="6" class="empty">
                No events recorded for this run.
            </td>
        </tr>
        """

    rows = []

    for event in events:
        elapsed = _event_elapsed_seconds(
            run["started_at"],
            event["occurred_at"],
        )

        rows.append(
            """
            <tr>
                <td>{elapsed}</td>
                <td class="{event_class}">
                    {event_type}
                </td>
                <td>{score}</td>
                <td>{lines}</td>
                <td>{level}</td>
                <td>{value}</td>
            </tr>
            """.format(
                elapsed=fmt_duration(round(elapsed)),
                event_class=_event_class(event["type"]),
                event_type=html.escape(event["type"] or "-"),
                score=fmt_score(event["score"]),
                lines=(
                    "-"
                    if event["lines"] is None
                    else event["lines"]
                ),
                level=(
                    "-"
                    if event["level"] is None
                    else event["level"]
                ),
                value=(
                    "-"
                    if event["value"] is None
                    else event["value"]
                ),
            )
        )

    return "".join(rows)


def _chart_data(run, events):
    result = []

    for event in events:
        elapsed = _event_elapsed_seconds(
            run["started_at"],
            event["occurred_at"],
        )

        result.append({
            "seconds": round(elapsed, 3),
            "score": int(event["score"] or 0),
            "lines": int(event["lines"] or 0),
            "level": int(event["level"] or 0),
            "type": event["type"] or "",
        })

    return result


def render(db, run_id):
    data = Data(db)
    run = data.run(run_id)

    if run is None:
        return None

    events = data.run_events(run_id)
    current_player = data.current_player()

    rate = tetris_rate(
        run["tetrises"],
        run["final_lines"],
    )
    spl = score_per_line(
        run["final_score"],
        run["final_lines"],
    )

    chart_json = json.dumps(_chart_data(run, events))

    body = """
    <a class="back-link" href="/">← Dashboard</a>

    <div class="run-title">
        <h2>Run #{run_id}</h2>
        <h2 class="run-score">{score}</h2>
    </div>

    <div class="cards">
        <div class="card">
            <div class="label">Score / Line</div>
            <div class="value">{spl:,.0f}</div>
        </div>

        <div class="card">
            <div class="label">Lines</div>
            <div class="value">{lines}</div>
        </div>

        <div class="card">
            <div class="label">Tetris Rate</div>
            <div class="value">{rate:.1f}%</div>
        </div>

        <div class="card">
            <div class="label">Game Time</div>
            <div class="value">{duration}</div>
        </div>
    </div>

    <section>
        <div class="run-chart-card">
            <div class="run-chart-header">
                <div>
                    <div class="label">Run progression</div>
                    <div class="muted">
                        Score and lines over elapsed game time
                    </div>
                </div>

                <div class="run-legend">
                    <span class="legend-item">
                        <span
                            class="legend-line"
                            style="background: var(--nord8)"
                        ></span>
                        Score
                    </span>
                    <span class="legend-item">
                        <span
                            class="legend-line"
                            style="background: var(--nord14)"
                        ></span>
                        Lines
                    </span>
                    <span class="legend-item">
                        <span
                            class="legend-line"
                            style="background: var(--nord13)"
                        ></span>
                        Tetris
                    </span>
                </div>
            </div>

            <div class="run-chart-container">
                <svg
                    id="run-chart"
                    class="run-chart"
                    viewBox="0 0 1000 280"
                    preserveAspectRatio="none"
                ></svg>
                <div
                    id="run-tooltip"
                    class="run-tooltip"
                ></div>
            </div>
        </div>
    </section>

    <section>
        <h2>Run Details</h2>
        <div class="table-wrap">
            <table>
                <thead>
                    <tr>
                        <th>Player</th>
                        <th>Start Lv</th>
                        <th>End Lv</th>
                        <th>Tetrises</th>
                        <th>Date</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>{player}</td>
                        <td>{start_level}</td>
                        <td>{end_level}</td>
                        <td>{tetrises}</td>
                        <td>{date}</td>
                        <td>{status}</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </section>

    <section>
        <h2>Events</h2>
        <div class="table-wrap">
            <table>
                <thead>
                    <tr>
                        <th>Time</th>
                        <th>Event</th>
                        <th>Score</th>
                        <th>Lines</th>
                        <th>Level</th>
                        <th>Value</th>
                    </tr>
                </thead>
                <tbody>
                    {events}
                </tbody>
            </table>
        </div>
    </section>

    <footer>
        Run UUID: {run_uuid}
    </footer>

    <script>
        const events = {chart_json};
        const startLevel = {start_level};

        (function () {{
            const svg = document.getElementById("run-chart");
            const tooltip = document.getElementById("run-tooltip");

            if (!svg || !tooltip || !events.length) {{
                return;
            }}

            const NS = "http://www.w3.org/2000/svg";
            const W = 1000;
            const H = 280;
            const PAD_X = 16;
            const PAD_Y = 18;
            const LEVEL_LABEL_Y = 18;
            const CHART_TOP = 34;

            const maxSeconds = Math.max(
                ...events.map(event => event.seconds),
                1
            );
            const maxScore = Math.max(
                ...events.map(event => event.score),
                1
            );
            const maxLines = Math.max(
                ...events.map(event => event.lines),
                1
            );

            function x(seconds) {{
                return PAD_X +
                    (seconds / maxSeconds) *
                    (W - PAD_X * 2);
            }}

            function y(value, max) {{
                return H - PAD_Y -
                    (value / max) *
                    (H - PAD_Y - CHART_TOP);
            }}

            [0.25, 0.5, 0.75].forEach(part => {{
                const line = document.createElementNS(
                    NS,
                    "line"
                );

                const yy =
                    H - PAD_Y -
                    part * (H - PAD_Y - CHART_TOP);

                line.setAttribute("x1", PAD_X);
                line.setAttribute("x2", W - PAD_X);
                line.setAttribute("y1", yy);
                line.setAttribute("y2", yy);
                line.setAttribute(
                    "stroke",
                    "var(--border)"
                );
                line.setAttribute(
                    "stroke-width",
                    "1"
                );

                svg.appendChild(line);
            }});

            const series = [
                {{
                    key: "score",
                    max: maxScore,
                    color: "var(--nord8)"
                }},
                {{
                    key: "lines",
                    max: maxLines,
                    color: "var(--nord14)"
                }}
            ];

            /*
             * Score and lines only change at recorded events.
             * Draw a step chart so values stay flat between events and
             * jump exactly at the event timestamp.
             */
            series.forEach(item => {{
                if (!events.length) {{
                    return;
                }}

                const path = document.createElementNS(NS, "path");
                const first = events[0];
                let d =
                    `M ${{x(first.seconds)}} ` +
                    `${{y(first[item.key], item.max)}}`;

                events.slice(1).forEach(event => {{
                    const xx = x(event.seconds);
                    const yy = y(event[item.key], item.max);

                    d += ` H ${{xx}}`;
                    d += ` V ${{yy}}`;
                }});

                path.setAttribute("d", d);
                path.setAttribute("fill", "none");
                path.setAttribute("stroke", item.color);
                path.setAttribute("stroke-width", "3");
                path.setAttribute(
                    "vector-effect",
                    "non-scaling-stroke"
                );
                path.setAttribute(
                    "stroke-linejoin",
                    "round"
                );
                path.setAttribute(
                    "stroke-linecap",
                    "round"
                );

                svg.appendChild(path);
            }});

            /* Show the starting level at the left edge. */
            const startLevelLabel =
                document.createElementNS(NS, "text");

            startLevelLabel.setAttribute("x", PAD_X);
            startLevelLabel.setAttribute("y", LEVEL_LABEL_Y);
            startLevelLabel.setAttribute("fill", "var(--nord9)");
            startLevelLabel.setAttribute("font-size", "13");
            startLevelLabel.setAttribute("font-weight", "700");
            startLevelLabel.setAttribute(
                "font-family",
                "-apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
            );
            startLevelLabel.textContent = "LV" + startLevel;

            svg.appendChild(startLevelLabel);

            /*
             * Draw level changes as vertical dashed lines with labels.
             * These are deliberately drawn before the Tetris markers so
             * the markers remain visually on top.
             */
            events.forEach(event => {{
                if (event.type !== "level_change") {{
                    return;
                }}

                const xx = x(event.seconds);

                const levelLine =
                    document.createElementNS(
                        NS,
                        "line"
                    );

                levelLine.setAttribute("x1", xx);
                levelLine.setAttribute("x2", xx);
                levelLine.setAttribute("y1", CHART_TOP);
                levelLine.setAttribute(
                    "y2",
                    H - PAD_Y
                );
                levelLine.setAttribute(
                    "stroke",
                    "var(--nord9)"
                );
                levelLine.setAttribute(
                    "stroke-width",
                    "1.5"
                );
                levelLine.setAttribute(
                    "stroke-dasharray",
                    "6 5"
                );
                levelLine.setAttribute(
                    "opacity",
                    "0.8"
                );
                levelLine.setAttribute(
                    "vector-effect",
                    "non-scaling-stroke"
                );

                svg.appendChild(levelLine);

                const label =
                    document.createElementNS(
                        NS,
                        "text"
                    );

                label.setAttribute(
                    "x",
                    Math.min(xx + 6, W - 48)
                );
                label.setAttribute(
                    "y",
                    LEVEL_LABEL_Y
                );
                label.setAttribute(
                    "fill",
                    "var(--nord9)"
                );
                label.setAttribute(
                    "font-size",
                    "13"
                );
                label.setAttribute(
                    "font-weight",
                    "700"
                );
                label.setAttribute(
                    "font-family",
                    "-apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
                );
                label.textContent =
                    "LV" + event.level;

                svg.appendChild(label);
            }});

            /*
             * Tetrises remain yellow markers on the score line.
             */
            events.forEach(event => {{
                if (event.type !== "tetris") {{
                    return;
                }}

                const circle =
                    document.createElementNS(
                        NS,
                        "circle"
                    );

                circle.setAttribute(
                    "cx",
                    x(event.seconds)
                );
                circle.setAttribute(
                    "cy",
                    y(event.score, maxScore)
                );
                circle.setAttribute("r", "5");
                circle.setAttribute(
                    "fill",
                    "var(--nord13)"
                );

                circle.addEventListener(
                    "mousemove",
                    mouseEvent => {{
                        tooltip.innerHTML =
                            `<strong>Tetris</strong><br>` +
                            `Score: ${{
                                event.score.toLocaleString()
                            }}<br>` +
                            `Lines: ${{event.lines}}<br>` +
                            `Level: ${{event.level}}`;

                        tooltip.style.display =
                            "block";

                        const box =
                            svg.getBoundingClientRect();

                        tooltip.style.left =
                            (
                                mouseEvent.clientX -
                                box.left +
                                12
                            ) + "px";

                        tooltip.style.top =
                            (
                                mouseEvent.clientY -
                                box.top +
                                12
                            ) + "px";
                    }}
                );

                circle.addEventListener(
                    "mouseleave",
                    () => {{
                        tooltip.style.display =
                            "none";
                    }}
                );

                svg.appendChild(circle);
            }});
        }})();
    </script>
    """.format(
        run_id=run["id"],
        score=fmt_score(run["final_score"]),
        spl=spl,
        lines=run["final_lines"],
        rate=rate,
        duration=fmt_duration(run["game_seconds"]),
        player=html.escape(run["player"]),
        start_level=run["start_level"],
        end_level=run["end_level"],
        tetrises=run["tetrises"],
        date=html.escape(fmt_date(run["ended_at"])),
        status=html.escape(
            run["validation_status"] or "-"
        ),
        events=_events_html(run, events),
        run_uuid=html.escape(run["run_uuid"] or "-"),
        chart_json=chart_json,
    )

    return page(
        "Run #{} · Tetris Tracker".format(run["id"]),
        body,
        current_player=current_player,
        refresh=False,
    )