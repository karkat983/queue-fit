"""Open-model load with true Poisson arrivals (exponential gaps), as a cross-check on k6,
whose arrival-rate executor spaces requests evenly.

    python scripts/poisson_load.py --rate 40 --duration 60 --out results/raw/poisson_rate40.csv
    python scripts/poisson_load.py --rate 40 --service exponential   # client-drawn Exp(0.05 s) delays

Arrival times are drawn up front, and each request is started at its time on a thread pool
large enough that the client never delays an arrival (checked: `late_ms` per request).
"""
import argparse
import csv
import pathlib
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from src.config import load_config, resolve  # noqa: E402


def schedule(rate: float, duration: float, seed: int) -> np.ndarray:
    """Poisson arrival times in [0, duration)."""
    rng = np.random.default_rng(seed)
    gaps = rng.exponential(1 / rate, int(rate * duration * 1.5) + 10)
    times = np.cumsum(gaps)
    return times[times < duration]


def delays(n: int, mode: str, mean: float, seed: int) -> np.ndarray:
    """Per-request sleep the server is asked for: constant or exponential with the given mean."""
    if mode == "constant":
        return np.full(n, mean)
    rng = np.random.default_rng(seed + 1)
    return np.minimum(rng.exponential(mean, n), 10.0)      # httpbin caps /delay at 10 s


def fire(url: str, due: float, t0: float) -> tuple[float, float, int]:
    late = max(0.0, time.perf_counter() - (t0 + due))
    start = time.perf_counter()
    try:
        with urllib.request.urlopen(url, timeout=60) as resp:
            resp.read()
            status = resp.status
    except Exception:
        status = 0
    return late, time.perf_counter() - start, status


def run(base_url: str, rate: float, duration: float, mode: str, mean: float, seed: int, workers: int):
    arrivals = schedule(rate, duration, seed)
    asks = delays(len(arrivals), mode, mean, seed)
    rows = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        t0 = time.perf_counter()
        futures = []
        for due, ask in zip(arrivals, asks, strict=True):
            wait = t0 + due - time.perf_counter()
            if wait > 0:
                time.sleep(wait)
            futures.append((due, ask, pool.submit(fire, f"{base_url}/delay/{ask:.4f}", due, t0)))
        for due, ask, fut in futures:
            late, latency, status = fut.result()
            rows.append({"arrival_s": round(due, 6), "delay_asked_s": round(ask, 6),
                         "latency_s": round(latency, 6), "late_ms": round(late * 1000, 3), "status": status})
    return rows


def main() -> None:
    cfg = load_config()
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--rate", type=float, required=True)
    parser.add_argument("--duration", type=float, default=60)
    parser.add_argument("--service", choices=["constant", "exponential"], default="constant")
    parser.add_argument("--mean", type=float, default=0.05, help="mean delay asked of the server (s)")
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--workers", type=int, default=256)
    parser.add_argument("--out")
    args = parser.parse_args()

    rows = run(cfg["service"]["base_url"], args.rate, args.duration, args.service, args.mean, args.seed,
               args.workers)
    out = resolve(args.out or f"results/raw/poisson_{args.service}_rate{args.rate:g}.csv")
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    lat = np.array([r["latency_s"] for r in rows if r["status"] == 200]) * 1000
    late = np.array([r["late_ms"] for r in rows])
    print(f"rate={args.rate:g}/s {args.service}: n={len(rows)} ok={len(lat)} "
          f"p50={np.median(lat):.1f}ms p95={np.quantile(lat, 0.95):.1f}ms "
          f"max client lateness={late.max():.1f}ms -> {out}")


if __name__ == "__main__":
    main()
