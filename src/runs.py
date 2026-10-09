"""Judge whether a run measured a stable queue, an overloaded one, or a broken client."""


def classify_run(row: dict, baseline_p50_ms: float, rho_estimate: float | None = None) -> str:
    """'ok', 'overloaded' or 'client_limited' for one sweep row.

    - overloaded: requests failed, or k6 had to drop arrivals, or the median latency is more
      than 5x the zero-load median: the queue grew during the run, so the result describes a
      transient, not a steady state, and must not be fitted as one.
    - client_limited: k6 dropped arrivals although the service was clearly below capacity
      (rho_estimate < 0.9): the load generator, not the server, was the bottleneck.
    """
    dropped = int(row.get("dropped") or 0)
    error_rate = float(row.get("error_rate") or 0)
    p50 = float(row["lat_p50_ms"])
    if dropped and rho_estimate is not None and rho_estimate < 0.9 and p50 < 2 * baseline_p50_ms:
        return "client_limited"
    if error_rate > 0.01 or dropped or p50 > 5 * baseline_p50_ms:
        return "overloaded"
    return "ok"
