from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Optional

from tetris_tracker.models import GameState
from tetris_tracker.storage import Storage


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Tracker:
    def __init__(
        self,
        collector,
        storage: Storage,
        poll_interval: float = 0.05,
        verbose: bool = True,
    ):
        self.collector = collector
        self.storage = storage
        self.poll_interval = poll_interval
        self.verbose = verbose

        self.run_id: Optional[int] = None
        self.last_state: Optional[GameState] = None
        self.clears = {1: 0, 2: 0, 3: 0, 4: 0}

        # Start: require a few consecutive gameplay samples.
        self.playing_samples = 0
        self.start_threshold = 3

        # End: require a persistent top-out signal.
        self.top_out_samples = 0
        self.top_out_threshold = 3

    def log(self, message: str) -> None:
        if self.verbose:
            print(message, flush=True)

    def notify(self, message: str) -> None:
        notify = getattr(self.collector, "notify", None)
        if callable(notify):
            try:
                notify(message)
            except Exception:
                pass

    def validate_run(self, state: GameState):
        errors = []

        event_lines = (
            self.clears[1]
            + self.clears[2] * 2
            + self.clears[3] * 3
            + self.clears[4] * 4
        )

        if event_lines != state.lines:
            errors.append(
                f"line mismatch: events={event_lines}, final={state.lines}"
            )

        if state.score < 0:
            errors.append(
                f"invalid score: {state.score}"
            )

        if state.lines < 0:
            errors.append(
                f"invalid lines: {state.lines}"
            )

        if state.level < 0:
            errors.append(
                f"invalid level: {state.level}"
            )

        if errors:
            return "warning", "; ".join(errors)

        return "valid", None

    def collector_reports_top_out(self, state: GameState) -> bool:
        fn = getattr(self.collector, "is_top_out", None)
        return bool(fn(state)) if callable(fn) else False

    def start_run(self, state: GameState) -> None:
        self.run_id = self.storage.start_run(state, _now())
        self.clears = {1: 0, 2: 0, 3: 0, 4: 0}
        self.top_out_samples = 0

        self.storage.add_event(
            self.run_id,
            _now(),
            "game_start",
            state,
        )

        self.log(
            f"[start] run={self.run_id} level={state.level} "
            f"score={state.score} lines={state.lines}"
        )
        self.notify("Tetris Tracker: Tracking started")

    def finish_run(self, state: GameState) -> None:
        if self.run_id is None:
            return

        run_id = self.run_id

        self.storage.add_event(
            run_id,
            _now(),
            "game_over",
            state,
        )

        validation_status, validation_error = self.validate_run(state)

        is_pb = self.storage.finish_run(
            run_id,
            _now(),
            state,
            self.clears,
            validation_status,
            validation_error,            
        )

        self.log(
            f"[end] run={run_id} score={state.score} "
            f"lines={state.lines} tetrises={self.clears[4]} pb={is_pb}"
        )

        if is_pb:
            self.notify(f"Tetris Tracker: NEW PB! {state.score} pts")
        else:
            self.notify(f"Tetris Tracker: Run saved - {state.score} pts")

        self.run_id = None
        self.playing_samples = 0
        self.top_out_samples = 0

    def record_line_clear(self, state: GameState, line_delta: int) -> None:
        if self.run_id is None:
            return

        names = {
            1: "single",
            2: "double",
            3: "triple",
            4: "tetris",
        }

        event_name = names.get(line_delta)
        if event_name is None:
            self.log(
                f"[warn] unexpected line delta={line_delta} "
                f"score={state.score} lines={state.lines}"
            )
            return

        self.clears[line_delta] += 1

        self.storage.add_event(
            self.run_id,
            _now(),
            event_name,
            state,
            value=line_delta,
            payload={
                "clear_count_raw": state.clear_count,
            },
        )

        self.log(
            f"[{event_name}] score={state.score} "
            f"lines={state.lines} level={state.level} "
            f"(raw_clear={state.clear_count})"
        )

    def process(self, state: GameState) -> None:
        previous = self.last_state

        # Start detection only matters while no run is active.
        if self.run_id is None:
            if state.playing:
                self.playing_samples += 1
            else:
                self.playing_samples = 0

            if (
                state.playing
                and self.playing_samples >= self.start_threshold
            ):
                self.start_run(state)

        if self.run_id is not None and previous is not None:
            # Use the persistent total line counter as source of truth.
            # The transient clear_count byte can be sampled mid-animation and
            # is therefore only retained as diagnostic metadata.
            line_delta = state.lines - previous.lines

            if 1 <= line_delta <= 4:
                self.record_line_clear(state, line_delta)
            elif line_delta < 0:
                # A reset should not happen inside a valid run; keep it visible
                # for diagnostics rather than inventing a clear event.
                self.log(
                    f"[warn] lines decreased {previous.lines} -> {state.lines}"
                )
            elif line_delta > 4:
                self.log(
                    f"[warn] lines jumped {previous.lines} -> {state.lines}"
                )

            if (
                state.level != previous.level
                and 0 <= state.level <= 29
            ):
                self.storage.add_event(
                    self.run_id,
                    _now(),
                    "level_change",
                    state,
                    value=state.level,
                )

                self.log(
                    f"[level] {previous.level} -> {state.level} "
                    f"score={state.score} lines={state.lines}"
                )

            # Only a collector-confirmed, persistent top-out ends the run.
            if self.collector_reports_top_out(state):
                self.top_out_samples += 1
            else:
                self.top_out_samples = 0

            if self.top_out_samples >= self.top_out_threshold:
                self.finish_run(state)

        self.last_state = state

    def run_forever(self) -> None:
        self.log("tetris-tracker started, press Ctrl+C to stop")

        while True:
            state = self.collector.read_state()

            if state is not None:
                self.process(state)

            time.sleep(self.poll_interval)
