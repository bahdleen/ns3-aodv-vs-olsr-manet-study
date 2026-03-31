#!/usr/bin/env bash
set -euo pipefail

RUNS="${RUNS:-1000}"
NODES="${NODES:-20}"
SIMTIME="${SIMTIME:-60}"

OUT_BASE="${OUT_BASE:-$PWD/report_runs}"
TAG="$(date +%F_%H%M%S)"
COMPARE_DIR="${OUT_BASE}/mesh_compare_${TAG}"
mkdir -p "$COMPARE_DIR/plots"

cd "$(dirname "$0")"

# Ensure pandas
python3 - <<'PY'
import sys
try:
    import pandas  # noqa
except Exception:
    sys.exit("ERROR: pandas missing. Install with: pip install pandas")
PY

echo "== Running AODV (verbose) =="
RUNS="$RUNS" NODES="$NODES" SIMTIME="$SIMTIME" PROTOCOL="AODV" SKIP_BUILD=0 \
OUT_BASE="$OUT_BASE" ./run_mesh_metrics_report_pack_verbose.sh

AODV_OUT="$(ls -td ${OUT_BASE}/mesh_metrics_*_AODV 2>/dev/null | head -n 1)"
AODV_CSV="${AODV_OUT}/data/results.csv"

echo
echo "== Running OLSR (verbose) =="
RUNS="$RUNS" NODES="$NODES" SIMTIME="$SIMTIME" PROTOCOL="OLSR" SKIP_BUILD=1 \
OUT_BASE="$OUT_BASE" ./run_mesh_metrics_report_pack_verbose.sh

OLSR_OUT="$(ls -td ${OUT_BASE}/mesh_metrics_*_OLSR 2>/dev/null | head -n 1)"
OLSR_CSV="${OLSR_OUT}/data/results.csv"

echo
echo "== Comparison pack =="
cp -f "$AODV_CSV" "$COMPARE_DIR/aodv_results.csv"
cp -f "$OLSR_CSV" "$COMPARE_DIR/olsr_results.csv"

python3 - <<'PY'
import os, pandas as pd
import matplotlib.pyplot as plt

compare_dir = os.environ["COMPARE_DIR"]
plots_dir = os.path.join(compare_dir, "plots")

a = pd.read_csv(os.path.join(compare_dir, "aodv_results.csv")).sort_values("seed")
o = pd.read_csv(os.path.join(compare_dir, "olsr_results.csv")).sort_values("seed")

metrics = [
    ("throughput_mbps","Throughput (Mbps)","throughput_compare.png"),
    ("avg_delay_ms","Average Delay (ms)","delay_compare.png"),
    ("pdr_percent","Packet Delivery Ratio (%)","pdr_compare.png"),
    ("tx_packets","TX Packets","tx_packets_compare.png"),
    ("rx_packets","RX Packets","rx_packets_compare.png"),
]

for col, ylabel, fn in metrics:
    plt.figure()
    plt.plot(a["seed"], a[col], label="AODV")
    plt.plot(o["seed"], o[col], label="OLSR")
    plt.title(f"{ylabel} vs Seed (n={len(a)})")
    plt.xlabel("Seed (run)")
    plt.ylabel(ylabel)
    plt.legend()
    plt.savefig(os.path.join(plots_dir, fn), dpi=180, bbox_inches="tight")
    plt.close()

cols = ["throughput_mbps","avg_delay_ms","pdr_percent","tx_packets","rx_packets"]
summary = pd.concat(
    [a[cols].describe().T.assign(protocol="AODV"),
     o[cols].describe().T.assign(protocol="OLSR")],
    axis=0
)
summary.to_csv(os.path.join(compare_dir, "summary_stats.csv"))

with open(os.path.join(compare_dir, "summary.txt"), "w") as f:
    f.write("Mesh Metrics Comparison Summary\n")
    f.write(f"AODV rows: {len(a)} | OLSR rows: {len(o)}\n\n")
    for metric in ["throughput_mbps","avg_delay_ms","pdr_percent"]:
        f.write(f"{metric} mean: AODV={a[metric].mean():.6f} | OLSR={o[metric].mean():.6f}\n")
PY

echo "DONE ✅"
echo "AODV folder : $AODV_OUT"
echo "OLSR folder : $OLSR_OUT"
echo "COMPARE dir : $COMPARE_DIR"
echo "COMPARE plots: $COMPARE_DIR/plots"
