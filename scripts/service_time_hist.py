"""Histogram of zero-load latencies (results/service_time.csv) -> results/service_time_hist.png."""
import csv
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from src import plot_style  # noqa: E402
from src.plot_style import SERIES, SURFACE, TEXT_SECONDARY, plt  # noqa: E402


def main(src: str = "results/service_time.csv", out: str = "results/service_time_hist.png") -> None:
    with open(ROOT / src) as f:
        ms = [float(r["latency_s"]) * 1000 for r in csv.DictReader(f)]
    plot_style.apply()
    fig, ax = plt.subplots(figsize=(6.4, 3.6))
    ax.hist(ms, bins=30, color=SERIES[0], edgecolor=SURFACE, linewidth=2)
    mean = sum(ms) / len(ms)
    ax.axvline(mean, color=TEXT_SECONDARY, linewidth=1, linestyle="--")
    ax.annotate(f"mean {mean:.1f} ms", (mean, ax.get_ylim()[1] * 0.92), xytext=(6, 0),
                textcoords="offset points", color=TEXT_SECONDARY)
    ax.set_title(f"Service time at zero load, /delay/0.05 (n = {len(ms)})")
    ax.set_xlabel("latency (ms)")
    ax.set_ylabel("requests")
    fig.tight_layout()
    fig.savefig(ROOT / out)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
