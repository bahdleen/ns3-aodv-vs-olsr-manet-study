import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

csv_file = "results/csv/final1000_per_run_metrics.csv"
df = pd.read_csv(csv_file)

out_dir = Path("results/charts")
out_dir.mkdir(parents=True, exist_ok=True)

metrics = [
    ("throughput_mbps", "Throughput (Mbps)"),
    ("pdr_percent", "Packet Delivery Ratio (%)"),
    ("loss_percent", "Packet Loss (%)"),
    ("avg_delay_ms", "Average Delay (ms)"),
    ("avg_jitter_ms", "Average Jitter (ms)"),
    ("application_flow_count", "Application Flow Count"),
]

for col, title in metrics:
    grouped = df.groupby("protocol")[col].mean()

    plt.figure(figsize=(8, 5))
    grouped.plot(kind="bar")
    plt.ylabel(title)
    plt.title(f"AODV vs OLSR - {title}")
    plt.xticks(rotation=0)
    plt.tight_layout()
    filename = out_dir / f"{col}.png"
    plt.savefig(filename, dpi=200)
    plt.close()
    print(f"Created: {filename}")
