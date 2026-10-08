"""Arrival-rate grid for a sweep, as fractions of the service's estimated capacity c * mu."""
from src.mmc import capacity


def rate_grid(service_time_s: float, workers: int, fractions: list[float]) -> list[float]:
    """Rates (req/s, one decimal) at the given utilisations. Fractions above 1 overload the
    service on purpose: the run then shows the queue growing without bound."""
    mu = 1 / service_time_s
    return [round(f * capacity(mu, workers), 1) for f in fractions]
