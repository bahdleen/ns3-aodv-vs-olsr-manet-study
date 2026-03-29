#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   ./compare_mesh_metrics.sh <AODV_results.csv> <OLSR_results.csv> [out_dir]
#
# Example:
#   ./compare_mesh_metrics.sh \
#     report_runs/mesh_metrics_2026-02-22_112601/data/results.csv \
#     report_runs/mesh_metrics_2026-02-22_112705/data/results.csv

AODV_CSV="${1:-}"
OLSR_CSV="${2:-}"
OUT_DIR="${3:-$PWD/report_runs/mesh_compare_$(date +%F_%H%M%S)}"

if [[ -z "$AODV_CSV" || -z "$OLSR_CSV" ]]; then
  echo "ERROR: provide AODV and OLSR CSV paths."
  echo "Usage: $0 <AODV_results.csv> <OLSR_results.csv> [out_dir]"
  exit 1
fi

if [[ ! -f "$AODV_CSV" ]]; then echo "ERROR: missing $AODV_CSV"; exit 1; fi
if [[ ! -f "$OLSR_CSV" ]]; then echo "ERROR: missing $OLSR_CSV"; exit 1; fi

mkdir -p "$OUT_DIR"
PLOTS_DIR="$OUT_DIR/plots"
mkdir -p "$PLOTS_DIR"

cp -f "$AODV_CSV" "$OUT_DIR/aodv_results.csv"
cp -f "$OLSR_CSV" "$OUT_DIR/olsr_results.csv"

PY="$OUT_DIR/compare.py"
cat >"$PY" <<'PY'
import os, pandas as pd
import matplotlib.pyplot as plt

out_dir = os.environ["OUT_DIR"]
plots_dir = os.environ["PLOTS_DIR"]
aodv_path = os.path.join(out_dir, "aodv_results.csv")
olsr_path = os.path.join(out_dir, "olsr_results.csv")

a = pd.read_csv(aodv_path)
o = pd.read_csv(olsr_path)

# Ensure sorted by seed for nicer plots
a = a.sort_values("seed")
o = o.sort_values("seed")

metrics = [
    ("throughput_mbps", "Throughput (Mbps)", "throughput_compare.png"),
    ("avg_delay_ms", "Average Delay (ms)", "delay_compare.png"),
    ("pdr_percent", "Packet Delivery Ratio (%)", "pdr_compare.png"),
    ("tx_packets", "TX Packets", "tx_packets_compare.png"),
    ("rx_packets", "RX Packets", "rx_packets_compare.png"),
]

def plot_compare(col, ylabel, filename):
    plt.figure()
    plt.plot(a["seed"], a[col], label="AODV")
    plt.plot(o["seed"], o[col], label="OLSR")
    plt.title(f"{ylabel} vs Seed")
    plt.xlabel("Seed (run)")
    plt.ylabel(ylabel)
    plt.legend()
    plt.savefig(os.path.join(plots_dir, filename), dpi=180, bbox_inches="tight")
    plt.close()

for col, ylabel, fn in metrics:
    plot_compare(col, ylabel, fn)

# Summary table
def describe(df, name):
    cols = ["throughput_mbps","avg_delay_ms","pdr_percent","tx_packets","rx_packets"]
    d = df[cols].describe().T  # count mean std min 25% 50% 75% max
    d.insert(0, "protocol", name)
    return d

summary = pd.concat([describe(a,"AODV"), describe(o,"OLSR")], axis=0)
summary_path = os.path.join(out_dir, "summary_stats.csv")
summary.to_csv(summary_path, index=True)

# A small human readable summary text
txt_path = os.path.join(out_dir, "summary.txt")
with open(txt_path, "w") as f:
    f.write("Mesh Metrics Comparison Summary\n")
    f.write(f"AODV rows: {len(a)} | OLSR rows: {len(o)}\n\n")
    for metric in ["throughput_mbps","avg_delay_ms","pdr_percent"]:
        f.write(f"{metric} (mean): AODV={a[metric].mean():.6f} | OLSR={o[metric].mean():.6f}\n")
PY

python3 - <<PY
import sys
try:
    import pandas
except Exception:
    sys.exit("ERROR: pandas not installed. Install: pip install pandas")
PY

OUT_DIR="$OUT_DIR" PLOTS_DIR="$PLOTS_DIR" python3 "$PY"

echo "DONE ✅ Comparison pack created:"
echo "  $OUT_DIR"
echo "  Plots: $PLOTS_DIR"
echo "  Summary: $OUT_DIR/summary_stats.csv and $OUT_DIR/summary.txt"
