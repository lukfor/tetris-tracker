# tetris-tracker

Small extensible Tetris training logger.

## Install locally

```bash
cd tetris-tracker
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

Enable RetroArch Network Commands:

```ini
network_cmd_enable = "true"
network_cmd_port = "55355"
```

Run the built-in NES Tetris collector:

```bash
tetris-tracker --host 127.0.0.1 --port 55355 nes-retroarch
```

Choose a database:

```bash
tetris-tracker --db ./tetris.db --host 127.0.0.1 --port 55355 nes-retroarch
```

List installed collectors:

```bash
tetris-tracker --list-collectors
```

## Plugin collectors

Third-party packages register a collector using Python entry points:

```toml
[project.entry-points."tetris_tracker.collectors"]
my-collector = "my_package.collector:MyCollector"
```

A collector class implements:

```python
class MyCollector:
    name = "my-collector"

    def __init__(self, config):
        ...

    def read_state(self):
        ...
```

`read_state()` returns either `None` (source unavailable) or a
`tetris_tracker.models.GameState`.

The tracker core owns session detection, event generation and SQLite writes.
Collectors should only translate their source into normalized game state.

## Built-in NES RetroArch collector

Current RAM addresses are for Nintendo NES Tetris:

- level: `0x0044`
- phase: `0x0048`
- lines: `0x0050..0x0051`
- score: `0x0053..0x0055`
- lines currently being cleared: `0x0056`
- current piece: `0x0042`
- next piece: `0x00BF`
- board: `0x0400..0x04C7`

The collector polls RetroArch using `READ_CORE_MEMORY`.


## RetroArch OSD notifications

The built-in `nes-retroarch` collector uses RetroArch `SHOW_MSG` for lightweight feedback:

- on game start: `Tetris Tracker: Tracking started`
- after a successful database commit: `Tetris Tracker: Run saved - ... pts`
- after a new personal best: `Tetris Tracker: NEW PB! ... pts`

Notifications are best-effort. A notification failure never interrupts tracking.


## Replay-ready database schema

Version 0.3 adds the `piece_states` table for future board replay support.
The current NES RetroArch collector does **not** write piece snapshots yet.

Each future snapshot can store:

- `run_id`
- sequential `piece_index`
- timestamp
- current / next piece
- score, lines, level
- compact board state as a SQLite `BLOB`

This keeps replay data separate from high-level `events` and allows the
collector to add board snapshots later without changing the run schema.


## Efficient NES RetroArch polling

Version 0.4 reduces RetroArch memory requests substantially.

Instead of reading each value with an individual `READ_CORE_MEMORY` request,
the NES collector now reads one compact block from `0x0042` through `0x0056`
and extracts these values locally:

- current piece
- level
- game phase
- lines
- score
- lines currently being cleared

Only `next_piece` at `0x00BF` requires a second small memory read.

At the default 50 ms polling interval this reduces the collector from roughly
7 memory reads per poll to 2 memory reads per poll, while also making the
main gameplay values come from the same emulator snapshot.


## v0.5 gameplay detection fixes

- Restores `Storage.finish_run()`.
- Adds a `runs.status` column (`active`, `completed`, future `interrupted`).
- Does not create a run merely because the Tetris ROM/menu is open.
- Requires three consecutive gameplay samples before `game_start`.
- Ignores line-clear counters before a run is active.
- Prevents menu/initialization RAM values from becoming fake clear events.
- Keeps the final RAM score, including soft-drop points, when completing a run.


## v0.6 run state-machine fix

- Keeps the improved real-game start detection from v0.5.
- Separates start detection from end detection.
- Transient phase changes and line-clear animations no longer end a run.
- A run only ends after the collector reports a persistent top-out state.
- NES RetroArch currently confirms top-out using phase `10`, observed for
  several consecutive polls.


## v0.7 reliable line-clear detection

Line clears are now classified from the persistent `lines` counter instead of
the transient NES `clear_count` byte.

Examples:

- `lines +1` -> single
- `lines +2` -> double
- `lines +3` -> triple
- `lines +4` -> tetris

The raw `clear_count` value is still stored in the event `payload_json` for
debugging, but it no longer determines statistics.


## v0.8 player-ready database

- Adds a `players` table and `runs.player_id`.
- Creates temporary default player `Lukas`.
- Existing runs without a player are assigned to `Lukas` automatically.
- New runs are assigned to `Lukas`.
- Personal-best calculation is scoped to the player.
- Player selection/menu comes later.


## v0.8 database behavior

Version 0.8 does not migrate older schemas.

If the configured SQLite database does not already contain the v0.8
player-aware schema, the tracker:

1. renames the old database to `*.pre-0.8-YYYYMMDD-HHMMSS.bak`
2. creates a fresh database
3. creates the default player `Lukas`
4. records all new runs against that player

A valid existing v0.8 database is reused unchanged.
