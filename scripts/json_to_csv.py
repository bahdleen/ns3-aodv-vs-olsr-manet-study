import json
import csv
from pathlib import Path

INPUTS = [
    ("results/metrics/final1000_AODV_summary.json", "AODV"),
    ("results/metrics/final1000_OLSR_summary.json", "OLSR"),
]

OUT_DIR = Path("results/csv")
OUT_DIR.mkdir(parents=True, exist_ok=True)

PER_RUN_CSV = OUT_DIR / "final1000_per_run_metrics.csv"
SUMMARY_CSV = OUT_DIR / "final1000_summary_metrics.csv"

per_run_rows = []
summary_rows = []

for json_file, protocol in INPUTS:
    with open(json_file) as f:
        data = json.load(f)

    for run in data.get("per_run", []):
        per_run_rows.append({
            "protocol": protocol,
            "file": run.get("file"),
            "application_flow_count": run.get("application_flow_count"),
            "tx_packets": run.get("tx_packets"),
            "rx_packets": run.get("rx_packets"),
            "lost_packets": run.get("lost_packets"),
            "tx_bytes": run.get("tx_bytes"),
            "rx_bytes": run.get("rx_bytes"),
            "throughput_bps": run.get("throughput_bps"),
            "throughput_mbps": run.get("throughput_mbps"),
            "pdr_percent": run.get("pdr_percent"),
            "loss_percent": run.get("loss_percent"),
            "avg_delay_s": run.get("avg_delay_s"),
            "avg_delay_ms": run.get("avg_delay_ms"),
            "avg_jitter_s": run.get("avg_jitter_s"),
            "avg_jitter_ms": run.get("avg_jitter_ms"),
        })

    s = data.get("summary", {})
    summary_rows.append({
        "protocol": protocol,
        "runs": s.get("runs"),
        "avg_application_flow_count": s.get("avg_application_flow_count"),
        "avg_throughput_bps": s.get("avg_throughput_bps"),
        "avg_throughput_mbps": s.get("avg_throughput_mbps"),
        "avg_pdr_percent": s.get("avg_pdr_percent"),
        "avg_loss_percent": s.get("avg_loss_percent"),
        "avg_delay_s": s.get("avg_delay_s"),
        "avg_delay_ms": s.get("avg_delay_ms"),
        "avg_jitter_s": s.get("avg_jitter_s"),
        "avg_jitter_ms": s.get("avg_jitter_ms"),
        "avg_tx_packets": s.get("avg_tx_packets"),
        "avg_rx_packets": s.get("avg_rx_packets"),
        "avg_lost_packets": s.get("avg_lost_packets"),
    })

with open(PER_RUN_CSV, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(per_run_rows[0].keys()))
    writer.writeheader()
    writer.writerows(per_run_rows)

with open(SUMMARY_CSV, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(summary_rows[0].keys()))
    writer.writeheader()
    writer.writerows(summary_rows)

print(f"Created: {PER_RUN_CSV}")
print(f"Created: {SUMMARY_CSV}")
