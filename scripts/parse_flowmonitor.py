import argparse
import glob
import json
import os
import statistics
import xml.etree.ElementTree as ET


def ns_time_to_seconds(value: str) -> float:
    if not value:
        return 0.0

    value = value.strip().replace("+", "")

    if value.endswith("ns"):
        return float(value[:-2]) / 1e9
    if value.endswith("us"):
        return float(value[:-2]) / 1e6
    if value.endswith("ms"):
        return float(value[:-2]) / 1e3
    if value.endswith("s"):
        return float(value[:-1])

    return float(value)


def build_flow_classifier_map(root):
    """
    Build mapping:
    flowId -> {
        sourceAddress,
        destinationAddress,
        protocol,
        sourcePort,
        destinationPort
    }
    """
    flow_map = {}

    # Usually classifier entries are under Ipv4FlowClassifier
    classifier_flows = root.findall(".//Ipv4FlowClassifier/Flow")

    # Fallback in case layout differs
    if not classifier_flows:
        classifier_flows = root.findall(".//Flow")

    for flow in classifier_flows:
        flow_id = flow.attrib.get("flowId")
        if flow_id is None:
            continue

        flow_map[flow_id] = {
            "sourceAddress": flow.attrib.get("sourceAddress"),
            "destinationAddress": flow.attrib.get("destinationAddress"),
            "protocol": flow.attrib.get("protocol"),
            "sourcePort": int(flow.attrib.get("sourcePort", 0)),
            "destinationPort": int(flow.attrib.get("destinationPort", 0)),
        }

    return flow_map


def parse_flowmonitor_file(xml_file: str, sim_time: float, min_port: int, max_port: int) -> dict:
    tree = ET.parse(xml_file)
    root = tree.getroot()

    classifier_map = build_flow_classifier_map(root)

    tx_packets = 0
    rx_packets = 0
    lost_packets = 0
    tx_bytes = 0
    rx_bytes = 0
    delay_sum_s = 0.0
    jitter_sum_s = 0.0
    flow_count = 0
    included_flow_ids = []

    stats_flows = root.findall(".//FlowStats/Flow")

    for flow in stats_flows:
        flow_id = flow.attrib.get("flowId")
        if flow_id is None:
            continue

        flow_info = classifier_map.get(flow_id, {})
        protocol = flow_info.get("protocol")
        destination_port = flow_info.get("destinationPort", 0)

        # Keep only experiment UDP application flows
        if protocol != "17":
            continue

        if not (min_port <= destination_port <= max_port):
            continue

        flow_count += 1
        included_flow_ids.append(int(flow_id))

        tx_packets += int(flow.attrib.get("txPackets", 0))
        rx_packets += int(flow.attrib.get("rxPackets", 0))
        lost_packets += int(flow.attrib.get("lostPackets", 0))
        tx_bytes += int(flow.attrib.get("txBytes", 0))
        rx_bytes += int(flow.attrib.get("rxBytes", 0))
        delay_sum_s += ns_time_to_seconds(flow.attrib.get("delaySum", "0ns"))
        jitter_sum_s += ns_time_to_seconds(flow.attrib.get("jitterSum", "0ns"))

    throughput_bps = (rx_bytes * 8) / sim_time if sim_time > 0 else 0.0
    throughput_mbps = throughput_bps / 1_000_000

    pdr_percent = (rx_packets / tx_packets * 100) if tx_packets > 0 else 0.0
    loss_percent = ((tx_packets - rx_packets) / tx_packets * 100) if tx_packets > 0 else 0.0

    avg_delay_s = (delay_sum_s / rx_packets) if rx_packets > 0 else 0.0
    avg_delay_ms = avg_delay_s * 1000

    avg_jitter_s = (jitter_sum_s / rx_packets) if rx_packets > 0 else 0.0
    avg_jitter_ms = avg_jitter_s * 1000

    return {
        "file": os.path.basename(xml_file),
        "application_flow_count": flow_count,
        "included_flow_ids": included_flow_ids,
        "tx_packets": tx_packets,
        "rx_packets": rx_packets,
        "lost_packets": lost_packets,
        "tx_bytes": tx_bytes,
        "rx_bytes": rx_bytes,
        "throughput_bps": throughput_bps,
        "throughput_mbps": throughput_mbps,
        "pdr_percent": pdr_percent,
        "loss_percent": loss_percent,
        "avg_delay_s": avg_delay_s,
        "avg_delay_ms": avg_delay_ms,
        "avg_jitter_s": avg_jitter_s,
        "avg_jitter_ms": avg_jitter_ms,
    }


def summarise_runs(results: list) -> dict:
    if not results:
        return {}

    return {
        "runs": len(results),
        "avg_application_flow_count": statistics.mean(r["application_flow_count"] for r in results),
        "avg_throughput_bps": statistics.mean(r["throughput_bps"] for r in results),
        "avg_throughput_mbps": statistics.mean(r["throughput_mbps"] for r in results),
        "avg_pdr_percent": statistics.mean(r["pdr_percent"] for r in results),
        "avg_loss_percent": statistics.mean(r["loss_percent"] for r in results),
        "avg_delay_s": statistics.mean(r["avg_delay_s"] for r in results),
        "avg_delay_ms": statistics.mean(r["avg_delay_ms"] for r in results),
        "avg_jitter_s": statistics.mean(r["avg_jitter_s"] for r in results),
        "avg_jitter_ms": statistics.mean(r["avg_jitter_ms"] for r in results),
        "avg_tx_packets": statistics.mean(r["tx_packets"] for r in results),
        "avg_rx_packets": statistics.mean(r["rx_packets"] for r in results),
        "avg_lost_packets": statistics.mean(r["lost_packets"] for r in results),
    }


def main():
    parser = argparse.ArgumentParser(description="Parse ns-3 FlowMonitor XML files")
    parser.add_argument("--pattern", required=True, help="Glob pattern for XML files")
    parser.add_argument("--simTime", type=float, required=True, help="Simulation time in seconds")
    parser.add_argument("--protocol", default="UNKNOWN", help="Protocol label")
    parser.add_argument("--output", required=True, help="Output JSON file")
    parser.add_argument("--minPort", type=int, default=9000, help="Minimum application destination port")
    parser.add_argument("--maxPort", type=int, default=9004, help="Maximum application destination port")
    parser.add_argument(
        "--print-json",
        action="store_true",
        help="Print the full JSON payload to stdout after writing the file",
    )
    args = parser.parse_args()

    files = sorted(glob.glob(args.pattern))
    if not files:
        raise FileNotFoundError(f"No files matched pattern: {args.pattern}")

    per_run = [
        parse_flowmonitor_file(f, args.simTime, args.minPort, args.maxPort)
        for f in files
    ]

    summary = summarise_runs(per_run)

    output = {
        "protocol": args.protocol,
        "simulation_time_s": args.simTime,
        "file_pattern": args.pattern,
        "application_port_range": [args.minPort, args.maxPort],
        "per_run": per_run,
        "summary": summary,
    }

    output_dir = os.path.dirname(args.output)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(args.output, "w") as f:
        json.dump(output, f, indent=2)

    if args.print_json:
        print(json.dumps(output, indent=2))
    else:
        print(
            f"Wrote {args.output} for protocol={args.protocol} with {len(per_run)} runs."
        )


if __name__ == "__main__":
    main()
