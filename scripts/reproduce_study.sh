#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

./ns3 build

python3 scripts/run_batch.py \
  --protocols AODV OLSR \
  --runs 1000 \
  --start-run 1 \
  --label final1000 \
  --raw-dir results/raw \
  --n-nodes 20 \
  --n-flows 2 \
  --sim-time 70 \
  --area-x 300 \
  --area-y 300 \
  --min-speed 1 \
  --max-speed 3 \
  --pause-time 2 \
  --server-start-time 1 \
  --client-start-time 10 \
  --packet-size 512 \
  --data-rate 1Mbps

./scripts/rebuild_results.sh
