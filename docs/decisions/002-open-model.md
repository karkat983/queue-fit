# ADR 002: open-model load (arrival rate), not closed-model load (virtual users)

**Status:** accepted (2026-10-09)

## Context

k6 can generate load two ways:

- **Closed model** (`vus` / `ramping-vus`): N virtual users each send a request, wait for the
  response, then send the next. The arrival rate is N / (response time), so when the server
  slows down, the load *drops* automatically.
- **Open model** (`constant-arrival-rate`): requests start at a fixed rate λ regardless of how
  long earlier requests take, the way independent users arrive at a real service.

## Decision

Use the open model. Queueing formulas take the arrival rate λ as an input that does not depend
on the response time. A closed-model test hides the knee: as latency grows, the generator backs
off, utilisation never approaches 1, and the latency curve looks flatter than the service
really is ("coordinated omission"). The open model keeps λ fixed, so queueing delay shows up in
latency exactly as the model predicts.

## Consequences

- k6 must have enough VUs to keep issuing requests while many are in flight; the script
  allocates generously and the parser records `dropped_iterations`, which must be 0 for a run
  to count (a non-zero value means the client, not the server, limited the load).
- k6's arrival-rate executor spaces requests **evenly** (inter-arrival SCV ca² ~ 0), not as a
  Poisson process (ca² = 1). Even spacing produces less queueing than Poisson at the same λ.
  A Python Poisson generator (`scripts/poisson_load.py`) provides true exponential gaps as a
  cross-check, and ca² enters the Allen-Cunneen fit.
