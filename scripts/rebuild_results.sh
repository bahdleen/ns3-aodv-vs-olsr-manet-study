#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

python3 scripts/parse_flowmonitor.py \
  --pattern "results/raw/final1000_AODV_*.xml" \
  --simTime 70 \
  --protocol AODV \
  --output results/metrics/final1000_AODV_summary.json \
  --minPort 9000 \
  --maxPort 9001

python3 scripts/parse_flowmonitor.py \
  --pattern "results/raw/final1000_OLSR_*.xml" \
  --simTime 70 \
  --protocol OLSR \
  --output results/metrics/final1000_OLSR_summary.json \
  --minPort 9000 \
  --maxPort 9001

python3 scripts/json_to_csv.py
python3 scripts/make_graphs.py
python3 scripts/make_distribution_graphs.py

if [[ "${RUN_AI_SUMMARY:-0}" == "1" ]]; then
  python3 scripts/ask_ai.py
fi

echo "Study outputs rebuilt under results/."
