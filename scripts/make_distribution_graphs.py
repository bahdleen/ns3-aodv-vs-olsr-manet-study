import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

csv_file = "results/csv/final1000_per_run_metrics.csv"
df = pd.read_csv(csv_file)

out_dir = Path("results/charts/distributions")
out_dir.mkdir(parents=True, exist_ok=True)

# Add run index extracted from filename
def extract_run_number(filename: str) -> int:
    # expects names like final1000_AODV_123.xml
    base = filename.replace(".xml", "")
    return int(base.split("_")[-1])

df["run_number"] = df["file"].apply(extract_run_number)

# -------------------------
# 1. Boxplots
# -------------------------
boxplot_metrics = [
    ("throughput_mbps", "Throughput (Mbps)"),
    ("pdr_percent", "Packet Delivery Ratio (%)"),
    ("loss_percent", "Packet Loss (%)"),
    ("avg_delay_ms", "Average Delay (ms)"),
    ("avg_jitter_ms", "Average Jitter (ms)"),
    ("application_flow_count", "Application Flow Count"),
]

for col, title in boxplot_metrics:
    plt.figure(figsize=(8, 5))
    data = [
        df[df["protocol"] == "AODV"][col].dropna(),
        df[df["protocol"] == "OLSR"][col].dropna()
    ]
    try:
        plt.boxplot(data, tick_labels=["AODV", "OLSR"])
    except TypeError:
        plt.boxplot(data, labels=["AODV", "OLSR"])
    plt.ylabel(title)
    plt.title(f"Distribution of {title} Across 1000 Runs")
    plt.tight_layout()
    filename = out_dir / f"boxplot_{col}.png"
    plt.savefig(filename, dpi=200)
    plt.close()
    print(f"Created: {filename}")

# -------------------------
# 2. Histograms
# -------------------------
hist_metrics = [
    ("throughput_mbps", "Throughput (Mbps)"),
    ("pdr_percent", "Packet Delivery Ratio (%)"),
    ("avg_delay_ms", "Average Delay (ms)"),
    ("application_flow_count", "Application Flow Count"),
]

for col, title in hist_metrics:
    plt.figure(figsize=(8, 5))
    plt.hist(df[df["protocol"] == "AODV"][col].dropna(), bins=30, alpha=0.6, label="AODV")
    plt.hist(df[df["protocol"] == "OLSR"][col].dropna(), bins=30, alpha=0.6, label="OLSR")
    plt.xlabel(title)
    plt.ylabel("Frequency")
    plt.title(f"Histogram of {title}")
    plt.legend()
    plt.tight_layout()
    filename = out_dir / f"hist_{col}.png"
    plt.savefig(filename, dpi=200)
    plt.close()
    print(f"Created: {filename}")

# -------------------------
# 3. Run-order line plots
# -------------------------
line_metrics = [
    ("throughput_mbps", "Throughput (Mbps)"),
    ("pdr_percent", "Packet Delivery Ratio (%)"),
    ("application_flow_count", "Application Flow Count"),
]

for col, title in line_metrics:
    plt.figure(figsize=(10, 5))
    for protocol in ["AODV", "OLSR"]:
        subset = df[df["protocol"] == protocol].sort_values("run_number")
        plt.plot(subset["run_number"], subset[col], label=protocol, linewidth=1)
    plt.xlabel("Run Number")
    plt.ylabel(title)
    plt.title(f"{title} Across Runs")
    plt.legend()
    plt.tight_layout()
    filename = out_dir / f"line_{col}.png"
    plt.savefig(filename, dpi=200)
    plt.close()
    print(f"Created: {filename}")

# -------------------------
# 4. Error-bar summary charts
# -------------------------
error_metrics = [
    ("throughput_mbps", "Throughput (Mbps)"),
    ("pdr_percent", "Packet Delivery Ratio (%)"),
    ("avg_delay_ms", "Average Delay (ms)"),
    ("avg_jitter_ms", "Average Jitter (ms)"),
]

for col, title in error_metrics:
    grouped = df.groupby("protocol")[col]
    means = grouped.mean()
    stds = grouped.std()

    plt.figure(figsize=(8, 5))
    plt.bar(means.index, means.values, yerr=stds.values, capsize=8)
    plt.ylabel(title)
    plt.title(f"{title} Mean ± Standard Deviation")
    plt.tight_layout()
    filename = out_dir / f"errorbar_{col}.png"
    plt.savefig(filename, dpi=200)
    plt.close()
    print(f"Created: {filename}")
