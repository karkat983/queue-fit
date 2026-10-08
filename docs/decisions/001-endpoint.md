# ADR 001: a sleep-based endpoint with client-controlled service times

**Status:** accepted (2026-10-09)

## Context

To test whether a queueing model can predict the latency knee, the service under test should
behave like the model's assumptions, or deviate from them in a known way. Two kinds of endpoint
were considered on httpbin:

1. **CPU-bound** (e.g. large `/bytes/N` or `/stream` responses). Realistic, but the service time
   depends on CPU contention. The load generator (k6) runs on the same machine as the service,
   so at high load the client and the server compete for the same cores, and the service rate
   would change with the arrival rate. That breaks the core assumption of a fixed μ.
2. **Sleep-based** (`/delay/x`). A gunicorn sync worker is busy for x seconds plus a few
   milliseconds of HTTP overhead, and sleeping uses no CPU. The worker is the only resource.

## Decision

Use `/delay/x` with sync workers, so:

- **Servers c** = number of gunicorn sync workers (known ground truth: 4 by default).
- **Service time** = x + overhead, where x is chosen by the client per request:
  - `constant` mode: x = 0.05 s for every request -> service is near-deterministic (M/D/c).
  - `exponential` mode: k6 draws x ~ Exp(mean 0.05 s) per request -> service is exponential with
    a known mean (M/M/c), apart from the small fixed overhead.
- The overhead (~6 ms measured at idle, docs/notes.md) is estimated from low-load runs and
  included in the fitted service time.

## Consequences

- The fit can be checked against known truth (c, μ), which a CPU-bound service would not allow.
- Running both modes shows how much the choice of model (M/M/c vs M/D/c) matters for predicting
  the knee: a central result, not a nuisance.
- The result is cleaner than production systems; the second-service phase (nginx, CPU limits,
  gevent workers) tests where the approach breaks.
- k6's constant-arrival-rate executor spaces arrivals evenly (ca² ~ 0), not Poisson. A Python
  Poisson load generator is added as a cross-check (plan commit 041), and the arrival variability
  is part of the Allen-Cunneen fit.
