# Findings

## Final 1000-Run Summary

| Metric | AODV | OLSR |
| --- | ---: | ---: |
| Average throughput (Mbps) | 0.418801 | 0.328218 |
| Average packet delivery ratio (%) | 23.162445 | 52.258269 |
| Average packet loss (%) | 76.837555 | 34.541731 |
| Average delay (ms) | 86.718743 | 57.873730 |
| Average jitter (ms) | 2.894094 | 1.340098 |
| Average active application flows | 2.000 | 1.264 |

## Reading The Results

- `OLSR` outperformed `AODV` on packet delivery ratio, loss, delay, and jitter.
- `AODV` maintained higher throughput and kept the configured flow count more consistently.
- The strongest performance gap appears in delivery efficiency: `OLSR` delivered more packets and lost fewer under the tested conditions.
- The main caution is that `OLSR` achieved those better delivery metrics while averaging fewer active application flows.

## Practical Interpretation

Within this scenario, `OLSR` looks stronger if the priority is per-flow delivery quality and latency behaviour. `AODV` looks stronger if the priority is maintaining the intended application-flow pattern more consistently. The published conclusion should therefore present a tradeoff, not a single universal winner.
