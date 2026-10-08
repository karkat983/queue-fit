"""M/M/c queue: Poisson arrivals (rate lam), exponential service (rate mu), c servers.

Notation follows Harchol-Balter (2013), ch. 14:
    a   = lam / mu          offered load, in "busy servers"
    rho = lam / (c * mu)    per-server utilisation; the queue is stable only if rho < 1
"""
import math


def utilisation(lam: float, mu: float, c: int) -> float:
    return lam / (c * mu)


def capacity(mu: float, c: int) -> float:
    """Maximum sustainable arrival rate, c * mu (the rate at which rho reaches 1)."""
    return c * mu


def rate_at(rho: float, mu: float, c: int) -> float:
    """Arrival rate that gives per-server utilisation rho; used to build load grids."""
    return rho * capacity(mu, c)


def is_stable(lam: float, mu: float, c: int) -> bool:
    return lam >= 0 and mu > 0 and c >= 1 and utilisation(lam, mu, c) < 1


def check_stable(lam: float, mu: float, c: int) -> None:
    if lam < 0 or mu <= 0 or c < 1:
        raise ValueError(f"need lam >= 0, mu > 0, c >= 1 (got lam={lam}, mu={mu}, c={c})")
    if utilisation(lam, mu, c) >= 1:
        raise ValueError(f"unstable: rho = {utilisation(lam, mu, c):.3f} >= 1")


def erlang_b(c: int, a: float) -> float:
    """Blocking probability of an M/M/c/c loss system, by the standard stable recursion

        B(0) = 1,   B(k) = a B(k-1) / (k + a B(k-1)),

    which never forms a**c or c! and so does not overflow for large c.
    """
    b = 1.0
    for k in range(1, c + 1):
        b = a * b / (k + a * b)
    return b


def erlang_c(c: int, a: float) -> float:
    """Probability that an arriving job has to wait (all c servers busy).

    Computed from Erlang B: C = c B / (c - a (1 - B)).
    """
    if a >= c:
        raise ValueError(f"unstable: offered load a = {a} >= c = {c}")
    b = erlang_b(c, a)
    return c * b / (c - a * (1 - b))


def mean_wait(lam: float, mu: float, c: int) -> float:
    """Mean time in queue, E[Wq] = C(c, a) / (c*mu - lam)."""
    check_stable(lam, mu, c)
    return erlang_c(c, lam / mu) / (c * mu - lam)


def mean_response(lam: float, mu: float, c: int) -> float:
    """Mean time in system, E[W] = E[Wq] + 1/mu."""
    return mean_wait(lam, mu, c) + 1 / mu


def wait_tail(t: float, lam: float, mu: float, c: int) -> float:
    """P(Wq > t): the queueing delay is 0 with prob 1 - C, else exponential with rate c*mu - lam."""
    check_stable(lam, mu, c)
    if t < 0:
        return 1.0
    return erlang_c(c, lam / mu) * math.exp(-(c * mu - lam) * t)


def response_tail(t: float, lam: float, mu: float, c: int) -> float:
    """P(T > t) for the response time T = Wq + S, with S ~ Exp(mu) independent of Wq.

    P(T > t) = e^{-mu t} + C * mu / (c mu - lam - mu) * (e^{-mu t} - e^{-(c mu - lam) t}),
    with the limit e^{-mu t} (1 + C mu t) when c mu - lam = mu. For c = 1 this reduces to
    the M/M/1 result e^{-(mu - lam) t}.
    """
    check_stable(lam, mu, c)
    if t < 0:
        return 1.0
    pw = erlang_c(c, lam / mu)
    gap = c * mu - lam - mu
    if abs(gap) < 1e-12 * mu:
        return math.exp(-mu * t) * (1 + pw * mu * t)
    return math.exp(-mu * t) + pw * mu / gap * (math.exp(-mu * t) - math.exp(-(c * mu - lam) * t))


def response_quantile(p: float, lam: float, mu: float, c: int) -> float:
    """The p-quantile of response time (e.g. p=0.95 for p95), by bisection on response_tail."""
    if not 0 < p < 1:
        raise ValueError("p must be in (0, 1)")
    target = 1 - p
    lo, hi = 0.0, 1.0 / mu
    while response_tail(hi, lam, mu, c) > target:
        hi *= 2
    for _ in range(200):
        mid = (lo + hi) / 2
        if response_tail(mid, lam, mu, c) > target:
            lo = mid
        else:
            hi = mid
        if hi - lo < 1e-12 * hi:
            break
    return (lo + hi) / 2


def allen_cunneen_wait(lam: float, mu: float, c: int, ca2: float = 1.0, cs2: float = 1.0) -> float:
    """Mean queueing delay of a G/G/c queue by the Allen-Cunneen approximation:

        E[Wq] ~ E[Wq]_{M/M/c} * (ca^2 + cs^2) / 2

    ca2, cs2 are the squared coefficients of variation of inter-arrival and service times
    (1 for exponential, 0 for constant). Exact for M/M/c; good for moderate-to-high load.
    """
    if ca2 < 0 or cs2 < 0:
        raise ValueError("squared coefficients of variation must be >= 0")
    return mean_wait(lam, mu, c) * (ca2 + cs2) / 2


def allen_cunneen_response(lam: float, mu: float, c: int, ca2: float = 1.0, cs2: float = 1.0) -> float:
    return allen_cunneen_wait(lam, mu, c, ca2, cs2) + 1 / mu
