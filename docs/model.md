# Queueing model

All formulas are implemented in `src/mmc.py` and checked against a discrete-event simulator
(`src/simulate.py`) in the tests.

## Notation

| Symbol | Meaning |
|--------|---------|
| λ | arrival rate (requests/s) |
| μ | service rate of one server (1 / mean service time) |
| c | number of servers (gunicorn sync workers) |
| a = λ/μ | offered load, in busy servers |
| ρ = λ/(cμ) | utilisation per server; the queue is stable only if ρ < 1 |
| Wq | time spent waiting in the queue |
| T = Wq + S | response time (wait + service) |

## M/M/c (Poisson arrivals, exponential service)

**Erlang B**, by the stable recursion (never forms aᶜ or c!):

    B(0) = 1,   B(k) = a·B(k−1) / (k + a·B(k−1))

**Erlang C** (probability an arrival has to wait):

    C(c, a) = c·B(c, a) / (c − a·(1 − B(c, a)))

**Mean wait and response time:**

    E[Wq] = C(c, a) / (cμ − λ)          E[T] = E[Wq] + 1/μ

**Waiting-time tail:** Wq is 0 with probability 1 − C, otherwise exponential with rate cμ − λ:

    P(Wq > t) = C(c, a) · e^{−(cμ−λ)t}

**Response-time tail** (Wq and the service time S ~ Exp(μ) are independent):

    P(T > t) = e^{−μt} + C · μ/(cμ − λ − μ) · (e^{−μt} − e^{−(cμ−λ)t})

with the limit e^{−μt}(1 + Cμt) when cμ − λ = μ. For c = 1 this reduces to the M/M/1 result
e^{−(μ−λ)t}. Quantiles (e.g. p95) are found by bisection on this tail.

## Beyond exponential service: Allen-Cunneen

Real services are rarely exponential. The Allen-Cunneen approximation for G/G/c scales the
M/M/c delay by the variability of arrivals (ca²) and service (cs²), the squared coefficients
of variation:

    E[Wq] ≈ E[Wq]_{M/M/c} · (ca² + cs²) / 2

- ca² = cs² = 1 gives M/M/c exactly.
- **M/D/c** (constant service, cs² = 0) is half the M/M/c delay. Exact for c = 1
  (Pollaczek-Khinchine); for c = 4 the tests find it within 10% of simulation on queueing
  delay and within 3% on response time at ρ = 0.6-0.9.

This matters here because the `/delay/0.05` endpoint has nearly constant service time
(see docs/notes.md), so M/D/c, not M/M/c, is the better-matched model.

## Why the latency curve has a knee

E[Wq] contains 1/(cμ − λ) = 1/(cμ(1 − ρ)), which grows without bound as ρ → 1. Response time is
flat while ρ is small (it is dominated by the service time 1/μ) and rises steeply as ρ
approaches 1. With more servers the curve stays flat for longer and then rises more sharply,
so the knee moves right and becomes more abrupt as c grows.

## Sources

- M. Harchol-Balter, *Performance Modeling and Design of Computer Systems*, Cambridge
  University Press, 2013 (ch. 14, M/M/k; ch. 23, M/G/1).
- L. Kleinrock, *Queueing Systems, Volume 1: Theory*, Wiley, 1975.
- A. O. Allen, *Probability, Statistics, and Queueing Theory*, 2nd ed., Academic Press, 1990
  (Allen-Cunneen approximation).
