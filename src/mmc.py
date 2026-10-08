"""M/M/c queue: Poisson arrivals (rate lam), exponential service (rate mu), c servers.

Notation follows Harchol-Balter (2013), ch. 14:
    a   = lam / mu          offered load, in "busy servers"
    rho = lam / (c * mu)    per-server utilisation; the queue is stable only if rho < 1
"""
def utilisation(lam: float, mu: float, c: int) -> float:
    return lam / (c * mu)


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
