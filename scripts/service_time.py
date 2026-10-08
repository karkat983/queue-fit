"""Measure service time at (near) zero load: one request at a time, so nothing ever queues.

    python scripts/service_time.py                  # 100 sequential requests to the configured endpoint
    python scripts/service_time.py --n 300 --out results/service_time.csv

Each latency here is service time plus network/HTTP overhead, with no queueing delay.
"""
import argparse
import csv
import pathlib
import sys
import time
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from src.config import load_config, resolve  # noqa: E402


def measure(url: str, n: int, pause: float = 0.05) -> list[float]:
    """Latency in seconds of n sequential GETs, with a pause between them."""
    out = []
    for _ in range(n):
        start = time.perf_counter()
        with urllib.request.urlopen(url, timeout=30) as resp:
            resp.read()
        out.append(time.perf_counter() - start)
        time.sleep(pause)
    return out


def main() -> None:
    cfg = load_config()
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--n", type=int, default=100)
    parser.add_argument("--endpoint", default=f"/delay/{cfg['service']['mean_delay_s']}")
    parser.add_argument("--out", default="results/service_time.csv")
    args = parser.parse_args()

    url = cfg["service"]["base_url"] + args.endpoint
    measure(url, 5)                               # warm up connections and workers
    samples = measure(url, args.n)
    out = resolve(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["endpoint", "latency_s"])
        writer.writerows([args.endpoint, f"{s:.6f}"] for s in samples)
    samples.sort()
    mean = sum(samples) / len(samples)
    print(f"{len(samples)} samples of {args.endpoint}: mean {mean * 1000:.2f} ms, "
          f"min {samples[0] * 1000:.2f}, median {samples[len(samples) // 2] * 1000:.2f}, "
          f"max {samples[-1] * 1000:.2f} ms -> {out}")


if __name__ == "__main__":
    main()
