"""Combine every sweep file into one tidy table: one row per (workers, service, rate).

    python -m src.combine            # results/sweep_*.csv -> results/results.csv

Repetitions are summarised by their median (robust to the occasional tail spike) and range.
Runs classified as overloaded are kept but flagged, because they describe a growing queue,
not a steady state.
"""
import glob
import pathlib

import pandas as pd

from src.config import load_config, resolve
from src.runs import classify_run

KEYS = ["workers", "service", "target_rps"]
METRICS = ["throughput_rps", "lat_mean_ms", "lat_p50_ms", "lat_p95_ms", "lat_p99_ms"]


def load_runs(paths: list[str], service_time_s: float) -> pd.DataFrame:
    """All runs from all files, with a status computed the same way for every file."""
    frames = []
    for path in paths:
        df = pd.read_csv(path)
        df["source"] = pathlib.Path(path).name
        frames.append(df)
    runs = pd.concat(frames, ignore_index=True)
    runs["rho_est"] = runs["target_rps"] * service_time_s / runs["workers"]
    records = runs.to_dict("records")
    runs["status"] = [classify_run(r, service_time_s * 1000, r["rho_est"]) for r in records]
    return runs


def summarise(runs: pd.DataFrame) -> pd.DataFrame:
    g = runs.groupby(KEYS)
    out = g[METRICS].median()
    out["p95_min_ms"] = g["lat_p95_ms"].min()
    out["p95_max_ms"] = g["lat_p95_ms"].max()
    out["reps"] = g.size()
    out["rho_est"] = g["rho_est"].first()
    out["overloaded_reps"] = g["status"].apply(lambda s: int((s == "overloaded").sum()))
    out["requests"] = g["requests"].sum()
    return out.reset_index().round(3)


def main() -> None:
    cfg = load_config()
    paths = sorted(glob.glob(str(resolve("results")) + "/sweep_*.csv"))
    table = summarise(load_runs(paths, cfg["sweep"]["service_time_s"]))
    out = resolve("results/results.csv")
    table.to_csv(out, index=False)
    print(f"{len(paths)} sweep files -> {len(table)} rows -> {out}")


if __name__ == "__main__":
    main()
