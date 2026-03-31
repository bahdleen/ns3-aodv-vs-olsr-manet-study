#!/usr/bin/env bash
set -euo pipefail

RUNS="${RUNS:-1000}"
START_SEED="${START_SEED:-1}"

NODES="${NODES:-20}"
PROTOCOL="${PROTOCOL:-AODV}"
SIMTIME="${SIMTIME:-60}"
AREAX="${AREAX:-50}"
AREAY="${AREAY:-30}"
SPEED="${SPEED:-1}"
INTERVAL="${INTERVAL:-0.2}"
PKTSIZE="${PKTSIZE:-200}"

# IMPORTANT: default OFF to avoid 1000 XML files
WRITE_FLOW_XML="${WRITE_FLOW_XML:-0}"

OUT_BASE="${OUT_BASE:-$PWD/report_runs}"
SKIP_BUILD="${SKIP_BUILD:-0}"

TS="$(date +%F_%H%M%S)"
OUT_DIR="${OUT_BASE}/mesh_metrics_${TS}_${PROTOCOL}"
LOG_DIR="${OUT_DIR}/logs"
DATA_DIR="${OUT_DIR}/data"
PLOT_DIR="${OUT_DIR}/plots"
mkdir -p "$LOG_DIR" "$DATA_DIR" "$PLOT_DIR"

CSV_PATH="${DATA_DIR}/results.csv"
BUILD_LOG="${OUT_DIR}/ns3_build.log"
MANIFEST="${OUT_DIR}/manifest.txt"

echo "============================================================"
echo " mesh-metrics VERBOSE Report Pack Runner"
echo "============================================================"
echo " Timestamp : $TS"
echo " OUT_DIR   : $OUT_DIR"
echo " RUNS      : $RUNS"
echo " SEEDS     : ${START_SEED}..$((START_SEED+RUNS-1))"
echo " PROTOCOL  : $PROTOCOL"
echo " NODES     : $NODES"
echo " SIMTIME   : $SIMTIME"
echo " AREA      : ${AREAX}x${AREAY} m"
echo " SPEED     : $SPEED m/s"
echo " INTERVAL  : $INTERVAL s"
echo " PKTSIZE   : $PKTSIZE bytes"
echo " FLOW XML  : $WRITE_FLOW_XML (0=off, 1=on)"
echo " CSV_PATH  : $CSV_PATH"
echo "============================================================"
echo

if [[ ! -x "./ns3" ]]; then
  echo "ERROR: ./ns3 not found. Run from ns-3 root (~/ns-3)."
  exit 1
fi

NS3_ROOT="$(pwd)"
NS3_RUNNER="${NS3_ROOT}/ns3"

if [[ "$SKIP_BUILD" == "0" ]]; then
  echo "== [1/4] Building ns-3 (./ns3 build) =="
  echo "Build log -> $BUILD_LOG"
  if ! "$NS3_RUNNER" build >"$BUILD_LOG" 2>&1; then
    echo "ERROR: build failed. Last lines:"
    tail -n 120 "$BUILD_LOG" || true
    exit 1
  fi
  echo "Build OK."
  echo
else
  echo "== [1/4] SKIP_BUILD=1 (skipping build) =="
  echo
fi

echo "== [2/4] Running experiments =="
rm -f "$CSV_PATH"

cat >"$MANIFEST" <<EOF2
mesh-metrics run manifest
timestamp=$TS
runs=$RUNS
start_seed=$START_SEED
protocol=$PROTOCOL
nodes=$NODES
simtime=$SIMTIME
areax=$AREAX
areay=$AREAY
speed=$SPEED
interval=$INTERVAL
pktsize=$PKTSIZE
writeFlowXml=$WRITE_FLOW_XML
csv=$CSV_PATH
EOF2

for i in $(seq 0 $((RUNS-1))); do
  SEED=$((START_SEED + i))
  LOG="${LOG_DIR}/seed_${SEED}.log"

  if [[ "$i" -eq 0 ]]; then
    CSV_HEADER="--csvHeader=1"
  else
    CSV_HEADER="--csvHeader=0"
  fi

  printf "[%04d/%04d] seed=%d | protocol=%s | nodes=%d | simTime=%s\n" \
    "$((i+1))" "$RUNS" "$SEED" "$PROTOCOL" "$NODES" "$SIMTIME"

  CMD="scratch/mesh-metrics \
    --nNodes=${NODES} \
    --protocol=${PROTOCOL} \
    --simTime=${SIMTIME} \
    --seed=${SEED} \
    --areaX=${AREAX} \
    --areaY=${AREAY} \
    --speed=${SPEED} \
    --interval=${INTERVAL} \
    --pktSize=${PKTSIZE} \
    --csvPath=${CSV_PATH} \
    --writeFlowXml=${WRITE_FLOW_XML} \
    ${CSV_HEADER}"

  echo "  ns3 run (cwd=$OUT_DIR): $CMD"

  # CRITICAL FIX: run from OUT_DIR so any flowmon.xml stays inside run folder
  pushd "$OUT_DIR" >/dev/null
  if ! "$NS3_RUNNER" run "$CMD" >"$LOG" 2>&1; then
    popd >/dev/null || true
    echo "ERROR: run failed at seed=$SEED"
    tail -n 120 "$LOG" || true
    exit 1
  fi
  popd >/dev/null

  if [[ ! -s "$CSV_PATH" ]]; then
    echo "ERROR: CSV not created/written: $CSV_PATH"
    exit 1
  fi
done

echo
echo "All runs complete ✅"
echo "CSV saved: $CSV_PATH"
echo

echo "== [3/4] Generating plots from CSV =="
head -n 2 "$CSV_PATH" || true
echo

PLOT_PY="${OUT_DIR}/plot_mesh_metrics.py"
cat >"$PLOT_PY" <<'PY'
import os, pandas as pd
import matplotlib.pyplot as plt

csv_path = os.environ["CSV_PATH"]
plot_dir = os.environ["PLOT_DIR"]
os.makedirs(plot_dir, exist_ok=True)

df = pd.read_csv(csv_path).sort_values("seed")

plots = [
    ("throughput_mbps", "Throughput (Mbps)", "throughput.png"),
    ("avg_delay_ms", "Average Delay (ms)", "avg_delay.png"),
    ("pdr_percent", "Packet Delivery Ratio (%)", "pdr.png"),
    ("tx_packets", "TX packets", "tx_packets.png"),
    ("rx_packets", "RX packets", "rx_packets.png"),
]

for col, ylabel, fn in plots:
    plt.figure()
    plt.plot(df["seed"], df[col])
    plt.title(f"{ylabel} vs Seed (n={len(df)})")
    plt.xlabel("Seed (run)")
    plt.ylabel(ylabel)
    plt.savefig(os.path.join(plot_dir, fn), dpi=180, bbox_inches="tight")
    plt.close()

summary = df[["throughput_mbps","avg_delay_ms","pdr_percent","tx_packets","rx_packets"]].describe().T
summary.to_csv(os.path.join(plot_dir, "summary_stats.csv"))

with open(os.path.join(plot_dir, "summary.txt"), "w") as f:
    f.write(f"Rows: {len(df)}\n")
    for metric in ["throughput_mbps","avg_delay_ms","pdr_percent"]:
        f.write(f"{metric} mean={df[metric].mean():.6f} std={df[metric].std():.6f}\n")
PY

python3 - <<'PY'
import sys
try:
    import pandas
except Exception:
    sys.exit("ERROR: pandas missing. Install with: pip install pandas")
PY

CSV_PATH="$CSV_PATH" PLOT_DIR="$PLOT_DIR" python3 "$PLOT_PY"

echo "Plots saved: $PLOT_DIR"
echo "Summary: $PLOT_DIR/summary_stats.csv and $PLOT_DIR/summary.txt"
echo

echo "== [4/4] Key locations =="
echo "OUT_DIR : $OUT_DIR"
echo "CSV     : $CSV_PATH"
echo "PLOTS   : $PLOT_DIR"
echo "LOGS    : $LOG_DIR"
echo
echo "DONE ✅"
