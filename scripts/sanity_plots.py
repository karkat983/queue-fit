"""Quick-look plots of the raw sweep data (results/results.csv), before any model is fitted.

    python scripts/sanity_plots.py   -> results/sanity_p95.png, results/sanity_throughput.png
"""
import pathlib
import sys

import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from src import plot_style  # noqa: E402
from src.plot_style import SERIES, TEXT_SECONDARY, plt  # noqa: E402


def main() -> None:
    df = pd.read_csv(ROOT / "results/results.csv").sort_values(["workers", "rho_est"])
    plot_style.apply()

    fig, ax = plt.subplots(figsize=(6.4, 4.0))
    for i, (workers, g) in enumerate(df.groupby("workers")):
        ax.plot(g["rho_est"], g["lat_p95_ms"], marker="o", color=SERIES[i], label=f"c = {workers}")
        ax.vlines(g["rho_est"], g["p95_min_ms"], g["p95_max_ms"], color=SERIES[i], linewidth=1, alpha=0.6)
    ax.set_yscale("log")
    ax.axvline(1.0, color=TEXT_SECONDARY, linewidth=1, linestyle="--")
    ax.set_title("p95 latency vs utilisation, constant service")
    fig.text(0.01, 0.01, "Points: median of 3 runs; bars: range over runs.", color=TEXT_SECONDARY, fontsize=8)
    ax.set_xlabel("estimated utilisation rho = rate x 55.1 ms / c")
    ax.set_ylabel("p95 latency (ms, log scale)")
    ax.legend(loc="upper left")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(ROOT / "results/sanity_p95.png")

    fig, ax = plt.subplots(figsize=(6.4, 4.0))
    for i, (workers, g) in enumerate(df.groupby("workers")):
        ax.plot(g["target_rps"], g["throughput_rps"], marker="o", color=SERIES[i], label=f"c = {workers}")
    top = df["target_rps"].max()
    ax.plot([0, top], [0, top], color=TEXT_SECONDARY, linewidth=1, linestyle="--", label="offered = served")
    ax.set_title("Throughput vs offered load")
    ax.set_xlabel("offered rate (requests/s)")
    ax.set_ylabel("completed requests/s")
    ax.legend(loc="upper left")
    fig.tight_layout()
    fig.savefig(ROOT / "results/sanity_throughput.png")
    print("wrote results/sanity_p95.png, results/sanity_throughput.png")


if __name__ == "__main__":
    main()
