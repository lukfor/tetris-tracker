from __future__ import annotations

import argparse
import sys

from tetris_tracker.plugin import CollectorConfig, discover_collectors
from tetris_tracker.storage import Storage
from tetris_tracker.tracker import Tracker


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tetris-tracker",
        description="Extensible classic Tetris training tracker",
    )

    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Collector host (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=55355,
        help="Collector port (default: 55355)",
    )
    parser.add_argument(
        "--db",
        default="./tetris.db",
        help="SQLite database path (default: ./tetris.db)",
    )
    parser.add_argument(
        "--poll",
        type=float,
        default=0.05,
        help="Polling interval in seconds (default: 0.05)",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Do not print tracking events",
    )
    parser.add_argument(
        "--list-collectors",
        action="store_true",
        help="List installed collector plugins and exit",
    )
    parser.add_argument(
        "collector",
        nargs="?",
        help="Collector plugin name, e.g. nes-retroarch",
    )

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    collectors = discover_collectors()

    if args.list_collectors:
        for name in sorted(collectors):
            print(name)
        return

    if not args.collector:
        parser.error("collector name missing; use --list-collectors")

    collector_cls = collectors.get(args.collector)

    if collector_cls is None:
        available = ", ".join(sorted(collectors)) or "(none)"
        parser.error(
            f"Unknown collector '{args.collector}'. "
            f"Available: {available}"
        )

    config = CollectorConfig(
        host=args.host,
        port=args.port,
        poll_interval=args.poll,
        options={},
    )

    collector = collector_cls(config)
    storage = Storage(args.db)

    tracker = Tracker(
        collector=collector,
        storage=storage,
        poll_interval=args.poll,
        verbose=not args.quiet,
    )

    try:
        tracker.run_forever()
    except KeyboardInterrupt:
        print("\nExited.", file=sys.stderr)
