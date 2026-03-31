# Results Layout

This directory contains the saved outputs for the published AODV vs OLSR comparison.

## Folders

- `raw/`: FlowMonitor XML files generated directly by ns-3 for each run.
- `metrics/`: Parsed JSON summaries, including per-run aggregates and final summary statistics.
- `csv/`: Flat tables exported from the JSON summaries for plotting and inspection.
- `charts/`: Summary and distribution plots used to present the comparison.
- `ai/`: Optional AI-assisted narrative summaries derived from the numeric outputs.

## Notes

- The `final1000_*` files correspond to the main reported experiment with 1000 runs per protocol.
- Additional labels such as `pilot`, `baseline`, `warm`, `test`, and `batch` are retained as earlier checkpoints from the same study.
- To regenerate the summary metrics and figures from the raw XML files, run `./scripts/rebuild_results.sh` from the repository root.
