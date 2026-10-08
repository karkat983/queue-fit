"""Turn a k6 end-of-test summary (JSON from handleSummary) into one flat CSV row."""
import json
import pathlib

FIELDS = [
    "duration_s", "requests", "throughput_rps", "failed", "error_rate", "dropped",
    "lat_min_ms", "lat_mean_ms", "lat_p50_ms", "lat_p90_ms", "lat_p95_ms", "lat_p99_ms", "lat_max_ms",
]


MAIN = "{scenario:main}"


def _metric(metrics: dict, name: str) -> dict:
    """Values of the main-scenario sub-metric if the run had a warm-up, else the plain metric."""
    return metrics.get(name + MAIN, metrics.get(name, {})).get("values", {})


def parse_summary(summary: dict, main_duration_s: float | None = None) -> dict:
    """Throughput, errors and latency (ms) of one k6 run, keyed by FIELDS.

    With a warm-up scenario, only the main scenario counts. k6 computes a sub-metric's rate
    over the whole test (warm-up included), so throughput is count / main_duration_s instead.
    """
    metrics = summary["metrics"]
    has_main = "http_reqs" + MAIN in metrics
    duration = _metric(metrics, "http_req_duration")
    reqs = _metric(metrics, "http_reqs")
    failed = _metric(metrics, "http_req_failed")
    # k6 only emits dropped_iterations when it actually dropped some.
    dropped = _metric(metrics, "dropped_iterations").get("count", 0)
    if has_main and main_duration_s is None:
        raise ValueError("run has a warm-up: pass main_duration_s to compute throughput")
    run_s = main_duration_s if has_main else summary["state"]["testRunDurationMs"] / 1000
    return {
        "duration_s": run_s,
        "requests": int(reqs["count"]),
        "throughput_rps": reqs["count"] / run_s if has_main else reqs["rate"],
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
