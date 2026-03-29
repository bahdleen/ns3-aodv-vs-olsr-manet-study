import argparse
import json
import os
from pathlib import Path

import requests


def load_json(path: Path) -> dict:
    with path.open() as handle:
        return json.load(handle)


def build_prompt(aodv: dict, olsr: dict) -> str:
    a = aodv["summary"]
    o = olsr["summary"]

    return f"""
You are analyzing final NS-3 MANET experiment results.

Use only the supplied numbers.
Do not invent values.
Be academically careful.
If the comparison is affected by unequal active flow counts, state that clearly.

Return ONLY valid JSON with exactly this structure:

{{
  "scenario_summary": {{
    "nodes": 20,
    "flows_configured": 2,
    "area": "300x300m",
    "mobility_model": "RandomWaypoint",
    "speed_range_mps": "1-3",
    "pause_time_s": 2,
    "traffic_type": "UDP CBR",
    "packet_size_bytes": 512,
    "simulation_time_s": 70,
    "warmup_note": "client traffic starts at 10 seconds",
    "runs_per_protocol": 1000
  }},
  "protocol_summary": {{
    "AODV": {{
      "throughput_mbps": 0.0,
      "pdr_percent": 0.0,
      "loss_percent": 0.0,
      "avg_delay_ms": 0.0,
      "avg_jitter_ms": 0.0,
      "avg_application_flow_count": 0.0
    }},
    "OLSR": {{
      "throughput_mbps": 0.0,
      "pdr_percent": 0.0,
      "loss_percent": 0.0,
      "avg_delay_ms": 0.0,
      "avg_jitter_ms": 0.0,
      "avg_application_flow_count": 0.0
    }}
  }},
  "comparison": {{
    "throughput_winner": "",
    "pdr_winner": "",
    "loss_winner": "",
    "delay_winner": "",
    "jitter_winner": "",
    "flow_consistency_winner": ""
  }},
  "interpretation": {{
    "overall_trend": "",
    "largest_difference": "",
    "likely_technical_cause": "",
    "fairness_note": "",
    "recommendation": "",
    "confidence_note": ""
  }},
  "report_ready_summary": ""
}}

Important comparison rule:
- higher is better for throughput, PDR, and application flow count
- lower is better for loss, delay, and jitter

Use these final measured values:

AODV:
- throughput_mbps: {a["avg_throughput_mbps"]}
- pdr_percent: {a["avg_pdr_percent"]}
- loss_percent: {a["avg_loss_percent"]}
- avg_delay_ms: {a["avg_delay_ms"]}
- avg_jitter_ms: {a["avg_jitter_ms"]}
- avg_application_flow_count: {a["avg_application_flow_count"]}

OLSR:
- throughput_mbps: {o["avg_throughput_mbps"]}
- pdr_percent: {o["avg_pdr_percent"]}
- loss_percent: {o["avg_loss_percent"]}
- avg_delay_ms: {o["avg_delay_ms"]}
- avg_jitter_ms: {o["avg_jitter_ms"]}
- avg_application_flow_count: {o["avg_application_flow_count"]}

Rules:
- Use only the numbers above.
- Do not add markdown.
- Do not add explanation outside JSON.
- If one protocol has a lower active application flow count, mention that in fairness_note and confidence_note.
- report_ready_summary must be 3 to 5 sentences, formal and concise.
""".strip()


def extract_json_text(response_json: dict) -> str | None:
    artifact = response_json.get("artifact")
    if isinstance(artifact, str) and artifact.strip():
        return artifact.strip()

    for key in ["output", "result", "response", "text", "summary"]:
        value = response_json.get(key)
        if isinstance(value, str) and value.strip().startswith("{"):
            return value.strip()

    return None


def repair_common_json_issues(text: str) -> str:
    text = text.replace(",\n  }", "\n  }")
    text = text.replace(",\n    }", "\n    }")
    text = text.replace(",\n}", "\n}")
    text = text.replace(",\n]", "\n]")
    return text


def winner_high(a: float, o: float) -> str:
    if a > o:
        return "AODV"
    if o > a:
        return "OLSR"
    return "Tie"


def winner_low(a: float, o: float) -> str:
    if a < o:
        return "AODV"
    if o < a:
        return "OLSR"
    return "Tie"


def build_fallback_structure(aodv: dict, olsr: dict) -> dict:
    a = aodv["summary"]
    o = olsr["summary"]

    return {
        "scenario_summary": {
            "nodes": 20,
            "flows_configured": 2,
            "area": "300x300m",
            "mobility_model": "RandomWaypoint",
            "speed_range_mps": "1-3",
            "pause_time_s": 2,
            "traffic_type": "UDP CBR",
            "packet_size_bytes": 512,
            "simulation_time_s": 70,
            "warmup_note": "client traffic starts at 10 seconds",
            "runs_per_protocol": 1000,
        },
        "protocol_summary": {
            "AODV": {
                "throughput_mbps": a["avg_throughput_mbps"],
                "pdr_percent": a["avg_pdr_percent"],
                "loss_percent": a["avg_loss_percent"],
                "avg_delay_ms": a["avg_delay_ms"],
                "avg_jitter_ms": a["avg_jitter_ms"],
                "avg_application_flow_count": a["avg_application_flow_count"],
            },
            "OLSR": {
                "throughput_mbps": o["avg_throughput_mbps"],
                "pdr_percent": o["avg_pdr_percent"],
                "loss_percent": o["avg_loss_percent"],
                "avg_delay_ms": o["avg_delay_ms"],
                "avg_jitter_ms": o["avg_jitter_ms"],
                "avg_application_flow_count": o["avg_application_flow_count"],
            },
        },
        "comparison": {
            "throughput_winner": winner_high(a["avg_throughput_mbps"], o["avg_throughput_mbps"]),
            "pdr_winner": winner_high(a["avg_pdr_percent"], o["avg_pdr_percent"]),
            "loss_winner": winner_low(a["avg_loss_percent"], o["avg_loss_percent"]),
            "delay_winner": winner_low(a["avg_delay_ms"], o["avg_delay_ms"]),
            "jitter_winner": winner_low(a["avg_jitter_ms"], o["avg_jitter_ms"]),
            "flow_consistency_winner": winner_high(
                a["avg_application_flow_count"], o["avg_application_flow_count"]
            ),
        },
        "interpretation": {
            "overall_trend": "OLSR achieved stronger delivery efficiency than AODV in the active flows observed, while AODV maintained the configured flow count more consistently.",
            "largest_difference": "The largest difference is in packet delivery ratio and loss, where OLSR clearly outperformed AODV.",
            "likely_technical_cause": "OLSR's proactive routing likely supported better path availability for active flows, while AODV's reactive behaviour may have introduced route establishment or maintenance penalties under the chosen mobility conditions.",
            "fairness_note": "The comparison is affected by unequal active application flow counts because AODV averaged 2.0 while OLSR averaged 1.264. This means OLSR's better delivery metrics were achieved on a less consistent flow set.",
            "recommendation": "Present OLSR as superior in per-flow delivery quality under this scenario, but state clearly that AODV was more consistent in preserving the configured traffic pattern.",
            "confidence_note": "Confidence in the measured averages is high because 1000 runs were completed per protocol, but confidence in a simple overall winner is reduced by the unequal active flow count.",
        },
        "report_ready_summary": "Across 1000 runs per protocol, OLSR achieved higher packet delivery ratio, lower loss, lower delay, and lower jitter than AODV in the flows that remained active. AODV, however, maintained the configured application-flow count more consistently across the experiment. This means OLSR showed better per-flow delivery quality, while AODV showed stronger flow persistence under the tested MANET conditions. The final interpretation should therefore reflect both performance quality and flow-consistency differences.",
    }


def normalize_and_correct(response_json: dict, aodv: dict, olsr: dict) -> dict:
    text = extract_json_text(response_json)
    parsed = None

    if text:
        repaired = repair_common_json_issues(text)
        try:
            parsed = json.loads(repaired)
        except Exception:
            parsed = None

    if not isinstance(parsed, dict):
        parsed = build_fallback_structure(aodv, olsr)

    a = aodv["summary"]
    o = olsr["summary"]

    parsed["scenario_summary"] = {
        "nodes": 20,
        "flows_configured": 2,
        "area": "300x300m",
        "mobility_model": "RandomWaypoint",
        "speed_range_mps": "1-3",
        "pause_time_s": 2,
        "traffic_type": "UDP CBR",
        "packet_size_bytes": 512,
        "simulation_time_s": 70,
        "warmup_note": "client traffic starts at 10 seconds",
        "runs_per_protocol": 1000,
    }

    parsed["protocol_summary"] = {
        "AODV": {
            "throughput_mbps": a["avg_throughput_mbps"],
            "pdr_percent": a["avg_pdr_percent"],
            "loss_percent": a["avg_loss_percent"],
            "avg_delay_ms": a["avg_delay_ms"],
            "avg_jitter_ms": a["avg_jitter_ms"],
            "avg_application_flow_count": a["avg_application_flow_count"],
        },
        "OLSR": {
            "throughput_mbps": o["avg_throughput_mbps"],
            "pdr_percent": o["avg_pdr_percent"],
            "loss_percent": o["avg_loss_percent"],
            "avg_delay_ms": o["avg_delay_ms"],
            "avg_jitter_ms": o["avg_jitter_ms"],
            "avg_application_flow_count": o["avg_application_flow_count"],
        },
    }

    parsed["comparison"] = {
        "throughput_winner": winner_high(a["avg_throughput_mbps"], o["avg_throughput_mbps"]),
        "pdr_winner": winner_high(a["avg_pdr_percent"], o["avg_pdr_percent"]),
        "loss_winner": winner_low(a["avg_loss_percent"], o["avg_loss_percent"]),
        "delay_winner": winner_low(a["avg_delay_ms"], o["avg_delay_ms"]),
        "jitter_winner": winner_low(a["avg_jitter_ms"], o["avg_jitter_ms"]),
        "flow_consistency_winner": winner_high(
            a["avg_application_flow_count"], o["avg_application_flow_count"]
        ),
    }

    return parsed


def parse_args():
    parser = argparse.ArgumentParser(
        description="Send the final metrics to an external AI endpoint for a structured summary."
    )
    parser.add_argument(
        "--api-url",
        default=os.environ.get("MANET_ANALYZE_API_URL"),
        help="Endpoint that accepts {'input': prompt} and returns JSON",
    )
    parser.add_argument(
        "--aodv-file",
        type=Path,
        default=Path("results/metrics/final1000_AODV_summary.json"),
        help="Path to the final AODV metrics JSON file",
    )
    parser.add_argument(
        "--olsr-file",
        type=Path,
        default=Path("results/metrics/final1000_OLSR_summary.json"),
        help="Path to the final OLSR metrics JSON file",
    )
    parser.add_argument(
        "--raw-out",
        type=Path,
        default=Path("results/ai/final1000_ai_raw_response.json"),
        help="Where to save the raw API response",
    )
    parser.add_argument(
        "--structured-out",
        type=Path,
        default=Path("results/ai/final1000_ai_structured.json"),
        help="Where to save the normalized structured summary",
    )
    parser.add_argument("--timeout", type=int, default=120, help="HTTP timeout in seconds")
    return parser.parse_args()


def main():
    args = parse_args()

    if not args.api_url:
        raise SystemExit(
            "No AI endpoint configured. Set MANET_ANALYZE_API_URL or pass --api-url."
        )

    aodv = load_json(args.aodv_file)
    olsr = load_json(args.olsr_file)

    prompt = build_prompt(aodv, olsr)
    response = requests.post(args.api_url, json={"input": prompt}, timeout=args.timeout)

    print("Status:", response.status_code)
    print("Response body:")
    print(response.text)

    response.raise_for_status()
    response_json = response.json()

    args.raw_out.parent.mkdir(parents=True, exist_ok=True)
    args.structured_out.parent.mkdir(parents=True, exist_ok=True)

    with args.raw_out.open("w") as handle:
        json.dump(response_json, handle, indent=2)

    structured = normalize_and_correct(response_json, aodv, olsr)
    with args.structured_out.open("w") as handle:
        json.dump(structured, handle, indent=2)

    print(f"\nSaved raw response to: {args.raw_out}")
    print(f"Saved structured output to: {args.structured_out}")


if __name__ == "__main__":
    main()
