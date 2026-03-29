import argparse
import subprocess
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run repeated ns-3 MANET comparison trials for one or more routing protocols."
    )
    parser.add_argument(
        "--protocols",
        nargs="+",
        default=["AODV", "OLSR"],
        help="Protocols to evaluate, e.g. AODV OLSR",
    )
    parser.add_argument("--runs", type=int, default=1000, help="Number of runs per protocol")
    parser.add_argument("--start-run", type=int, default=1, help="Starting RNG run number")
    parser.add_argument(
        "--label",
        default="final1000",
        help="Filename prefix for generated FlowMonitor XML files",
    )
    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=Path("results/raw"),
        help="Directory for raw FlowMonitor XML outputs",
    )
    parser.add_argument(
        "--failure-log",
        type=Path,
        default=Path("results/failed_runs.log"),
        help="Path to append failed runs",
    )
    parser.add_argument("--binary", default="scratch/manet_compare", help="ns-3 program to run")
    parser.add_argument("--n-nodes", type=int, default=20, help="Number of MANET nodes")
    parser.add_argument("--n-flows", type=int, default=2, help="Number of UDP flows")
    parser.add_argument("--sim-time", type=float, default=70.0, help="Simulation time in seconds")
    parser.add_argument("--area-x", type=float, default=300.0, help="Simulation area X dimension")
    parser.add_argument("--area-y", type=float, default=300.0, help="Simulation area Y dimension")
    parser.add_argument("--min-speed", type=float, default=1.0, help="Minimum node speed")
    parser.add_argument("--max-speed", type=float, default=3.0, help="Maximum node speed")
    parser.add_argument("--pause-time", type=float, default=2.0, help="Mobility pause time")
    parser.add_argument(
        "--server-start-time",
        type=float,
        default=1.0,
        help="UDP server application start time",
    )
    parser.add_argument(
        "--client-start-time",
        type=float,
        default=10.0,
        help="UDP client application start time",
    )
    parser.add_argument("--packet-size", type=int, default=512, help="UDP packet size in bytes")
    parser.add_argument("--data-rate", default="1Mbps", help="UDP client data rate")
    return parser.parse_args()


def build_cmd(args, protocol: str, run_number: int, output_path: Path) -> str:
    scenario_args = {
        "protocol": protocol,
        "run": run_number,
        "output": output_path,
        "nNodes": args.n_nodes,
        "nFlows": args.n_flows,
        "simTime": args.sim_time,
        "areaX": args.area_x,
        "areaY": args.area_y,
        "minSpeed": args.min_speed,
        "maxSpeed": args.max_speed,
        "pauseTime": args.pause_time,
        "serverStartTime": args.server_start_time,
        "clientStartTime": args.client_start_time,
        "packetSize": args.packet_size,
        "dataRate": args.data_rate,
    }
    segments = [args.binary]
    for key, value in scenario_args.items():
        segments.append(f"--{key}={value}")
    return " ".join(str(segment) for segment in segments)


def main():
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    raw_dir = repo_root / args.raw_dir
    raw_dir.mkdir(parents=True, exist_ok=True)

    failure_log = repo_root / args.failure_log
    failure_log.parent.mkdir(parents=True, exist_ok=True)
    if failure_log.exists():
        failure_log.unlink()

    total = len(args.protocols) * args.runs
    current = 0
    failures = []

    for protocol in args.protocols:
        for offset in range(args.runs):
            run_number = args.start_run + offset
            current += 1
            output_path = raw_dir / f"{args.label}_{protocol}_{run_number}.xml"
            cmd = build_cmd(args, protocol, run_number, output_path)
            print(f"[{current}/{total}] Running: {cmd}")

            result = subprocess.run(["./ns3", "run", cmd], cwd=repo_root, check=False)
            if result.returncode != 0:
                failures.append((protocol, run_number, result.returncode))
                with failure_log.open("a") as handle:
                    handle.write(f"{protocol},{run_number},{result.returncode}\n")

    print("Batch finished.")
    print(f"Failures: {len(failures)}")
    if failures:
        print(f"See {failure_log}")


if __name__ == "__main__":
    main()
