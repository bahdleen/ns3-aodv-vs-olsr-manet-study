# Methodology

## Objective

The goal of this study is to compare `AODV` and `OLSR` under the same MANET conditions in ns-3 and evaluate how each protocol behaves across repeated runs rather than relying on a single simulation outcome.

## Simulation Scenario

- Simulator: `ns-3`
- Scenario source: `scratch/manet_compare.cc`
- Number of nodes: `20`
- Routing protocols: `AODV`, `OLSR`
- Mobility model: `RandomWaypointMobilityModel`
- Area: `300m x 300m`
- Node speed range: `1-3 m/s`
- Pause time: `2s`
- Traffic type: `UDP CBR`
- Packet size: `512 bytes`
- Application data rate: `1 Mbps`
- Configured application flows: `2`
- Simulation time: `70s`
- Server start time: `1s`
- Client start time: `10s`
- Runs per protocol in the final experiment: `1000`

## Execution Pipeline

1. Run repeated trials with `python3 scripts/run_batch.py`.
2. Save one FlowMonitor XML file per run into `results/raw/`.
3. Parse the XML files with `python3 scripts/parse_flowmonitor.py`.
4. Export final summaries into CSV form with `python3 scripts/json_to_csv.py`.
5. Generate charts with `python3 scripts/make_graphs.py` and `python3 scripts/make_distribution_graphs.py`.
6. Optionally produce a structured narrative summary with `python3 scripts/ask_ai.py`.

## Metrics Reported

- Throughput
- Packet delivery ratio
- Packet loss
- Average delay
- Average jitter
- Active application flow count

## Interpretation Caveat

The final comparison shows a meaningful fairness issue: `OLSR` produced better delivery-oriented metrics on average, but it also had fewer active application flows than `AODV`. Any conclusion about a protocol "winning" should therefore be framed in terms of tradeoffs rather than a single absolute ranking.
