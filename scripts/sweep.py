"""Run the k6 load test once per (arrival rate, repetition) and keep every summary.

    python scripts/sweep.py                       # rates/duration/repetitions from config.yaml
    python scripts/sweep.py --rates 10 40 --reps 1 --duration 20s
    python scripts/sweep.py --dry-run             # print the k6 commands only

Summaries land in results/raw/c<workers>_rate<r>_rep<i>.json, and one row per run is
appended to results/raw/runs.csv.
"""
import argparse
import csv
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from src.config import load_config, resolve  # noqa: E402
from src.grid import rate_grid  # noqa: E402
from src.k6summary import FIELDS, load_summary, parse_summary  # noqa: E402

RUN_FIELDS = ["workers", "endpoint", "target_rps", "rep"] + FIELDS


def append_row(path: pathlib.Path, row: dict) -> None:
    new = not path.exists()
    with open(path, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=RUN_FIELDS)
        if new:
            writer.writeheader()
        writer.writerow(row)


def k6_command(base_url: str, endpoint: str, rate: float, duration: str, out: pathlib.Path) -> list[str]:
    return [
        "k6", "run", "-q",
        "-e", f"BASE_URL={base_url}",
        "-e", f"ENDPOINT={endpoint}",
        "-e", f"RATE={rate:g}",
        "-e", f"DURATION={duration}",
        "-e", f"OUT={out}",
        str(ROOT / "load" / "test.js"),
    ]


def main() -> None:
    cfg = load_config()
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    grid = rate_grid(cfg["sweep"]["service_time_s"], cfg["service"]["workers"], cfg["sweep"]["utilisations"])
    parser.add_argument("--rates", type=float, nargs="+", default=grid)
    parser.add_argument("--reps", type=int, default=cfg["sweep"]["repetitions"])
    parser.add_argument("--duration", default=cfg["sweep"]["duration"])
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    svc = cfg["service"]
    out_dir = resolve(cfg["sweep"]["out_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)
    for rep in range(1, args.reps + 1):
        for rate in args.rates:
            out = out_dir / f"c{svc['workers']}_rate{rate:g}_rep{rep}.json"
            cmd = k6_command(svc["base_url"], svc["endpoint"], rate, args.duration, out)
            if args.dry_run:
                print(" ".join(cmd))
                continue
            result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
            line = result.stdout.strip().splitlines()[-1] if result.stdout.strip() else ""
            print(f"rep {rep} {line}", flush=True)
            if result.returncode not in (0, 99):    # 99 = thresholds crossed; still a valid run
                print(result.stderr, file=sys.stderr)
                raise SystemExit(f"k6 failed at rate {rate}")
            row = {"workers": svc["workers"], "endpoint": svc["endpoint"], "target_rps": rate, "rep": rep}
            row.update(parse_summary(load_summary(out)))
            append_row(out_dir / "runs.csv", row)


if __name__ == "__main__":
    main()
