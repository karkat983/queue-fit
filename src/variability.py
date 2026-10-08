"""Variability of service and inter-arrival times, the inputs to the Allen-Cunneen model."""
import statistics


def scv(samples: list[float]) -> float:
    """Squared coefficient of variation: variance / mean^2 (1 for exponential, 0 for constant)."""
    if len(samples) < 2:
        raise ValueError("need at least two samples")
    mean = statistics.fmean(samples)
    return statistics.variance(samples) / mean**2

