import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Load results
df = pd.read_csv("results.csv")

# Make plots look professional
sns.set(style="whitegrid")
plt.rcParams["figure.figsize"] = (8, 5)

metrics = {
    "avg_delay_ms": "Average Delay (ms)",
    "throughput_mbps": "Throughput (Mbps)",
    "pdr_percent": "Packet Delivery Ratio (%)"
}

for column, label in metrics.items():
    plt.figure()
    sns.boxplot(data=df, x="protocol", y=column)
    plt.title(f"{label} Comparison")
    plt.xlabel("Routing Protocol")
    plt.ylabel(label)
    plt.tight_layout()
    plt.savefig(f"{column}.png", dpi=300)
    plt.close()

print("Graphs generated successfully.")
