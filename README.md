# AODV vs OLSR MANET Comparison in ns-3

This repository contains a comparative ns-3 study of two MANET routing protocols, `AODV` and `OLSR`, under the same mobile ad hoc network scenario. The workspace is still a full `ns-3` source tree, but the study-specific assets are now organized so the repository reads like a research project instead of an upstream simulator checkout.

## Study Summary

The published experiment uses:

- `20` wireless nodes
- `2` UDP CBR application flows
- `300m x 300m` simulation area
- `RandomWaypoint` mobility
- node speeds between `1` and `3 m/s`
- `2s` pause time
- `70s` simulation time
- clients starting at `10s`
- `1000` runs per protocol

The main simulation scenario is implemented in `scratch/manet_compare.cc`.

## Key Findings

| Metric | AODV | OLSR | Higher/Lower Is Better | Observed Winner |
| --- | ---: | ---: | --- | --- |
| Throughput (Mbps) | 0.4188 | 0.3282 | Higher | AODV |
| Packet Delivery Ratio (%) | 23.16 | 52.26 | Higher | OLSR |
| Packet Loss (%) | 76.84 | 34.54 | Lower | OLSR |
| Average Delay (ms) | 86.72 | 57.87 | Lower | OLSR |
| Average Jitter (ms) | 2.89 | 1.34 | Lower | OLSR |
| Average Active Application Flows | 2.000 | 1.264 | Higher | AODV |

The main interpretation is that `OLSR` delivered better packet-level quality on the flows that remained active, while `AODV` preserved the configured traffic pattern more consistently. That flow-count difference matters when discussing fairness, so the results should not be reduced to a single absolute winner.

## Repository Layout

```text
scratch/manet_compare.cc        Main ns-3 simulation scenario
scripts/run_batch.py            Batch runner for repeated protocol trials
scripts/parse_flowmonitor.py    FlowMonitor XML parser
scripts/json_to_csv.py          JSON-to-CSV conversion for final summaries
scripts/make_graphs.py          Summary comparison charts
scripts/make_distribution_graphs.py
                                Distribution plots across runs
scripts/rebuild_results.sh      Rebuild metrics and figures from saved XML files
scripts/reproduce_study.sh      Full study rerun entry point
results/raw/                    Raw FlowMonitor XML outputs
results/metrics/                Parsed JSON summaries
results/csv/                    Tabular exports
results/charts/                 Publication-ready figures
results/ai/                     Optional AI-assisted interpretation outputs
research/                       Methodology and findings notes
research/latex/                 LaTeX archive and browsable manuscript source
```

Early one-off helper scripts that were not part of the final published workflow were moved into `scripts/archive/`.

## Reproducing The Study

### 1. Build ns-3

```bash
./ns3 configure --enable-examples --enable-tests
./ns3 build
```

### 2. Install Python dependencies for the analysis pipeline

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-research.txt
```

### 3. Rebuild charts from the saved raw XML files

This is the quickest way to verify the published outputs:

```bash
./scripts/rebuild_results.sh
```

### 4. Rerun the full 1000-run experiment

This step is much slower because it regenerates the raw XML data first:

```bash
./scripts/reproduce_study.sh
```

## Optional AI Interpretation

The repository includes an optional post-processing script, `scripts/ask_ai.py`, for turning the numeric summaries into a short structured interpretation. It is disabled by default unless you provide an API URL through `MANET_ANALYZE_API_URL`.

## Manuscript Source

The LaTeX submission bundle is included at `research/latex/AODV_vs_OLSR_MANET_Comparison_in_ns_3.zip`.
The extracted source is also available under `research/latex/source/`, so GitHub can display files such as `research/latex/source/_main.tex` and `research/latex/source/references.bib` directly in the browser.

## Notes On Scope

- This repository keeps the full `ns-3` tree because the study was developed directly inside that environment.
- The research-specific content is concentrated in `scratch/`, `scripts/`, `results/`, and `research/`.
- Build artifacts, local virtual environments, and temporary report folders are intentionally ignored.

## License

The repository contains `ns-3`, which is licensed under `GPL-2.0-only`. See `LICENSE` for details.
