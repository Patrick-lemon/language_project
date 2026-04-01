#!/usr/bin/env bash
# Loads .env if present, then starts the tutor. From project directory:
#   chmod +x run_tutor.sh
#   ./run_tutor.sh

set -euo pipefail
cd "$(dirname "$0")"

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

exec python3 main_dialogue.py
