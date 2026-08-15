import html


CSS = r"""
:root {
    color-scheme: dark;

    --nord0: #2e3440;
    --nord1: #3b4252;
    --nord2: #434c5e;
    --nord3: #4c566a;
    --nord4: #d8dee9;
    --nord5: #e5e9f0;
    --nord6: #eceff4;
    --nord7: #8fbcbb;
    --nord8: #88c0d0;
    --nord9: #81a1c1;
    --nord10: #5e81ac;
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
}

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    background: var(--bg);
    color: var(--text);
    font-family:
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        sans-serif;
}

a {
    color: inherit;
}

main {
    width: min(1180px, calc(100% - 32px));
    margin: 0 auto;
    padding: 34px 0 60px;
}

header {
    display: flex;
    align-items: end;
    justify-content: space-between;
    gap: 24px;
    margin-bottom: 24px;
}

h1 {
    margin: 0;
    font-size: clamp(30px, 4vw, 44px);
    letter-spacing: -0.045em;
}

h2 {
    margin: 0 0 12px;
    font-size: 20px;
}

.subtitle,
.muted {
    color: var(--muted);
}

.subtitle {
    margin-top: 6px;
}

.header-meta {
    display: flex;
    align-items: center;
    gap: 12px;
}

.refresh {
    font-size: 13px;
}

.player-chip {
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
}

.player-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--nord14);
    box-shadow: 0 0 0 3px rgba(163, 190, 140, 0.12);
}

.cards {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 14px;
    margin: 24px 0 30px;
}

.card {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 18px;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.12);
}

.label {
    color: var(--muted);
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}

.value {
    margin-top: 7px;
    font-size: 28px;
    font-weight: 760;
    letter-spacing: -0.02em;
}

.cards .card:first-child .value {
    color: var(--accent);
}

section {
    margin-top: 28px;
}

.table-wrap {
    overflow-x: auto;
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 14px;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.12);
}

table {
    width: 100%;
    min-width: 850px;
    border-collapse: collapse;
}

th {
    padding: 12px 14px;
    text-align: left;
    background: var(--panel-2);
    color: var(--muted);
    font-size: 11px;
    font-weight: 650;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    border-bottom: 1px solid var(--border);
}

td {
    padding: 12px 14px;
    border-bottom: 1px solid var(--border);
    font-variant-numeric: tabular-nums;
}

tbody tr:last-child td {
    border-bottom: none;
}

tbody tr {
    transition: background 100ms ease;
}

tbody tr:hover {
    background: rgba(136, 192, 208, 0.07);
}

.rank {
    width: 42px;
    color: var(--muted);
}

.score,
.score-link {
    color: var(--score);
    font-weight: 750;
}

.score-link {
    text-decoration: none;
}

.score-link:hover {
    text-decoration: underline;
}

.empty {
    padding: 30px;
    text-align: center;
    color: var(--muted);
}

.valid {
    color: var(--nord14);
    font-weight: 900;
}

.warning {
    color: var(--nord13);
    font-weight: 900;
}

.unknown {
    color: var(--muted);
}

.back-link {
    display: inline-block;
    margin-bottom: 18px;
    color: var(--muted);
    text-decoration: none;
    font-size: 13px;
}

.back-link:hover {
    color: var(--text);
}

.run-title {
    display: flex;
    align-items: baseline;
    gap: 12px;
    flex-wrap: wrap;
}

.run-score {
    color: var(--score);
}

.run-chart-card {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 18px;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.12);
}

.run-chart-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    margin-bottom: 12px;
}

.run-legend {
    display: flex;
    gap: 16px;
    color: var(--muted);
    font-size: 12px;
}

.legend-item {
    display: inline-flex;
    align-items: center;
    gap: 6px;
}

.legend-line {
    width: 18px;
    height: 3px;
    border-radius: 2px;
}

.run-chart-container {
    position: relative;
}

.run-chart {
    width: 100%;
    height: 280px;
    display: block;
}

.run-tooltip {
    position: absolute;
    display: none;
    pointer-events: none;
    z-index: 10;
    background: var(--nord0);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 9px 11px;
    font-size: 12px;
    line-height: 1.5;
    white-space: nowrap;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.25);
}

.event-type {
    font-weight: 700;
}

.event-tetris {
    color: var(--nord13);
}

.event-level {
    color: var(--nord8);
}

footer {
    margin-top: 28px;
    color: var(--muted);
    font-size: 12px;
}

@media (max-width: 760px) {
    header {
        display: block;
    }

    .header-meta {
        margin-top: 12px;
        justify-content: space-between;
    }

    .cards {
        grid-template-columns: repeat(2, 1fr);
    }

    .run-chart-header {
        display: block;
    }

    .run-legend {
        margin-top: 10px;
    }
}
"""


def page(title, body, current_player=None, refresh=True):
    refresh_tag = (
        '<meta http-equiv="refresh" content="15">'
        if refresh
        else ""
    )

    player_html = ""
    if current_player:
        player_html = """
        <div class="player-chip">
            <span class="player-dot"></span>
            <span>{}</span>
        </div>
        """.format(html.escape(current_player))

    refresh_html = ""
    if refresh:
        refresh_html = """
        <div class="refresh muted">
            Refreshes every 15 seconds
        </div>
        """

    return """<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta
        name="viewport"
        content="width=device-width, initial-scale=1"
    >
    {refresh_tag}
    <title>{title}</title>
    <style>{css}</style>
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
                {player_html}
                {refresh_html}
            </div>
        </header>

        {body}
    </main>
</body>
</html>
""".format(
        refresh_tag=refresh_tag,
        title=html.escape(title),
        css=CSS,
        player_html=player_html,
        refresh_html=refresh_html,
        body=body,
    )
