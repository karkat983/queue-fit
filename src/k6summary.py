"""Turn a k6 end-of-test summary (JSON from handleSummary) into one flat CSV row."""
import json
import pathlib


def parse_summary(summary: dict) -> dict:
    """Throughput and latency (ms) of one k6 run."""
    metrics = summary["metrics"]
    duration = metrics["http_req_duration"]["values"]
    reqs = metrics["http_reqs"]["values"]
    return {
        "requests": int(reqs["count"]),
        "throughput_rps": reqs["rate"],
        "lat_p50_ms": duration["med"],
        "lat_p95_ms": duration["p(95)"],
    }


def load_summary(path: pathlib.Path | str) -> dict:
    with open(path) as f:
        return json.load(f)
