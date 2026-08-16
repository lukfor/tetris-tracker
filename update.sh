#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

echo "Updating Tetris Tracker..."

git pull --ff-only
python3 -m pip install --user .

echo "Done."