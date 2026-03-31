#!/usr/bin/env bash
set -euo pipefail

# =========================
# CONFIG (override at runtime)
# =========================
RUNS="${RUNS:-30}"
START_SEED="${START_SEED:-1}"

# Use your sim’s built-in args
NODES="${NODES:-20}"
PROTOCOL="${PROTOCOL:-AODV}"     # AODV or OLSR
SIMTIME="${SIMTIME:-60}"
AREAX="${AREAX:-50}"
AREAY="${AREAY:-30}"
SPEED="${SPEED:-1}"
INTERVAL="${INTERVAL:-0.2}"
PKTSIZE="${PKTSIZE:-200}"

OUT_BASE="${OUT_BASE:-$PWD/report_runs}"

# =========================
# Folder setup
# =========================
TS="$(date +%F_%H%M%S)"
OUT_DIR="${OUT_BASE}/mesh_metrics_${TS}"
LOG_DIR="${OUT_DIR}/logs"
DATA_DIR="${OUT_DIR}/data"
PLOT_DIR="${OUT_DIR}/plots"
mkdir -p "$LOG_DIR" "$DATA_DIR" "$PLOT_DIR"

CSV_PATH="${DATA_DIR}/results.csv"

echo "== mesh-metrics Report Pack Runner =="
echo "RUNS     : $RUNS"
echo "SEEDS    : ${START_SEED}..$((START_SEED+RUNS-1))"
echo "NODES    : $NODES"
echo "PROTOCOL : $PROTOCOL"
echo "SIMTIME  : $SIMTIME"
echo "CSV_PATH : $CSV_PATH"
echo "OUT_DIR  : $OUT_DIR"
echo

# =========================
# Build once
# =========================
if [[ ! -x "./ns3" ]]; then
  echo "ERROR: ./ns3 not found. Run this from the ns-3 root (~/ns-3)."
  exit 1
fi

echo "== Building (./ns3 build) =="
if ! ./ns3 build >"${OUT_DIR}/ns3_build.log" 2>&1; then
  echo "ERROR: build failed. Last lines:"
  tail -n 120 "${OUT_DIR}/ns3_build.log" || true
  exit 1
fi
echo "Build OK."
echo

# =========================
# Run experiments
# NOTE: mesh-metrics appends to CSV; we write header only once.
# =========================
echo "== Running experiments =="
rm -f "$CSV_PATH"

for i in $(seq 0 $((RUNS-1))); do
  SEED=$((START_SEED + i))
  LOG="${LOG_DIR}/seed_${SEED}.log"

  # header only for first run
  if [[ "$i" -eq 0 ]]; then
    CSV_HEADER="--csvHeader=1"
  else
    CSV_HEADER="--csvHeader=0"
  fi

  echo "Run $((i+1))/$RUNS (seed=$SEED)"
  ./ns3 run "scratch/mesh-metrics \
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
    ${CSV_HEADER}" >"$LOG" 2>&1 || {
      echo "ERROR: run failed for seed=$SEED. Last lines:"
      tail -n 120 "$LOG" || true
      exit 1
    }
done

echo
echo "All runs complete."
echo "CSV saved: $CSV_PATH"
echo

# =========================
# Plot from CSV (auto-detect numeric columns)
# Generates:
# - one plot per numeric metric vs seed/run index
# - optional comparison plot if both AODV+OLSR are run into separate folders (later)
# =========================
echo "== Generating plots =="
PLOT_PY="${OUT_DIR}/plot_from_csv.py"

cat >"$PLOT_PY" <<'PY'
import csv, os, math
import matplotlib.pyplot as plt

csv_path = os.environ["CSV_PATH"]
out_dir  = os.environ["PLOT_DIR"]
os.makedirs(out_dir, exist_ok=True)

def is_number(x):
    try:
        float(x)
        return True
    except:
        return False

rows = []
with open(csv_path, newline="") as f:
    r = csv.DictReader(f)
    headers = r.fieldnames or []
    for row in r:
        rows.append(row)

if not rows:
    raise SystemExit("CSV has no data rows.")

# Choose an x-axis column:
# Prefer 'seed' if present, else 'run', else row index
xcol = None
for candidate in ["seed", "Seed", "rngSeed", "run", "Run"]:
    if candidate in (headers or []):
        xcol = candidate
        break

xs = []
if xcol:
    for row in rows:
        v = row.get(xcol, "")
        xs.append(float(v) if is_number(v) else float(len(xs)+1))
else:
    xs = list(range(1, len(rows)+1))

# Determine numeric metric columns (exclude xcol)
numeric_cols = []
for h in headers:
    if h == xcol:
        continue
    # if at least half the rows parse as numbers, treat numeric
    vals = [row.get(h, "") for row in rows]
    ok = sum(1 for v in vals if is_number(v))
    if ok >= max(1, len(vals)//2):
        numeric_cols.append(h)

if not numeric_cols:
    raise SystemExit(
        "Could not detect numeric columns to plot.\n"
        "Open the CSV and tell me the column names, and I’ll hard-code them."
    )

def plot_one(col):
    ys = []
    for row in rows:
        v = row.get(col, "")
        ys.append(float(v) if is_number(v) else float("nan"))

    # filter NaNs
    x2, y2 = [], []
    for x, y in zip(xs, ys):
        if not (y is None or (isinstance(y, float) and math.isnan(y))):
            x2.append(x); y2.append(y)

    if not y2:
        return

    plt.figure()
    plt.plot(x2, y2)
    plt.title(col)
    plt.xlabel(xcol if xcol else "run_index")
    plt.ylabel(col)
    safe = "".join(c if c.isalnum() or c in "._-" else "_" for c in col)
    plt.savefig(os.path.join(out_dir, f"{safe}.png"), dpi=180, bbox_inches="tight")
    plt.close()

for col in numeric_cols:
    plot_one(col)

# Also output a simple summary table as text
summary_txt = os.path.join(out_dir, "summary.txt")
with open(summary_txt, "w") as f:
    f.write(f"Rows: {len(rows)}\n")
    f.write(f"X-axis: {xcol if xcol else 'run_index'}\n")
    f.write("Plotted columns:\n")
    for c in numeric_cols:
        f.write(f"  - {c}\n")

print("Plots written to:", out_dir)
print("Summary written to:", summary_txt)
PY

CSV_PATH="$CSV_PATH" PLOT_DIR="$PLOT_DIR" python3 "$PLOT_PY"
echo "Plots saved in: $PLOT_DIR"
echo
echo "DONE ✅ Report pack folder:"
echo "  $OUT_DIR"
