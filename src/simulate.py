"""Discrete-event simulation of a FCFS c-server queue, to check the formulas and the fits.

Arrivals are Poisson (rate lam) unless inter-arrival times are given; service times come from
a sampler, so the same code covers M/M/c (exponential), M/D/c (constant) and M/G/c.
"""
import heapq
from collections.abc import Callable
from dataclasses import dataclass

import numpy as np


@dataclass
class SimResult:
    waits: np.ndarray       # time in queue per job
    responses: np.ndarray   # time in system per job (wait + service)

    def mean_wait(self) -> float:
        return float(self.waits.mean())

    def mean_response(self) -> float:
        return float(self.responses.mean())

    def quantile(self, p: float) -> float:
        return float(np.quantile(self.responses, p))


def exponential(mu: float) -> Callable[[np.random.Generator, int], np.ndarray]:
    return lambda rng, n: rng.exponential(1 / mu, n)


def constant(mu: float) -> Callable[[np.random.Generator, int], np.ndarray]:
    return lambda rng, n: np.full(n, 1 / mu)


def simulate(
    lam: float,
    c: int,
    service: Callable[[np.random.Generator, int], np.ndarray],
    n_jobs: int = 200_000,
    warmup: int = 10_000,
    seed: int = 0,
    interarrivals: np.ndarray | None = None,
) -> SimResult:
    """Simulate n_jobs arrivals; the first `warmup` jobs are dropped from the result."""
    rng = np.random.default_rng(seed)
    gaps = interarrivals if interarrivals is not None else rng.exponential(1 / lam, n_jobs)
    arrivals = np.cumsum(gaps)
    services = service(rng, len(arrivals))
    free_at = [0.0] * c                 # min-heap of the times each server becomes free
    waits = np.empty(len(arrivals))
    for i, (t, s) in enumerate(zip(arrivals, services, strict=True)):
        start = max(t, heapq.heappop(free_at))
        waits[i] = start - t
        heapq.heappush(free_at, start + s)
    return SimResult(waits=waits[warmup:], responses=(waits + services)[warmup:])
