"""Turn a k6 end-of-test summary (JSON from handleSummary) into one flat CSV row."""
import json
import pathlib


FIELDS = [
    "duration_s", "requests", "throughput_rps", "failed", "error_rate", "dropped",
    "lat_min_ms", "lat_mean_ms", "lat_p50_ms", "lat_p90_ms", "lat_p95_ms", "lat_p99_ms", "lat_max_ms",
]


def parse_summary(summary: dict) -> dict:
    """Throughput, errors and latency (ms) of one k6 run, keyed by FIELDS."""
    metrics = summary["metrics"]
    duration = metrics["http_req_duration"]["values"]
    reqs = metrics["http_reqs"]["values"]
    failed = metrics.get("http_req_failed", {}).get("values", {})
    # k6 only emits dropped_iterations when it actually dropped some.
    dropped = metrics.get("dropped_iterations", {}).get("values", {}).get("count", 0)
    return {
        "duration_s": summary["state"]["testRunDurationMs"] / 1000,
        "requests": int(reqs["count"]),
        "throughput_rps": reqs["rate"],
        "failed": int(failed.get("passes", 0)),
        "error_rate": failed.get("rate", 0.0),
        "dropped": int(dropped),
        "lat_min_ms": duration["min"],
        "lat_mean_ms": duration["avg"],
        "lat_p50_ms": duration["med"],
        "lat_p90_ms": duration["p(90)"],
        "lat_p95_ms": duration["p(95)"],
        "lat_p99_ms": duration["p(99)"],
        "lat_max_ms": duration["max"],
    }


def load_summary(path: pathlib.Path | str) -> dict:
    with open(path) as f:
        return json.load(f)
