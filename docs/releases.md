# Releases

## v0.1-core (2026-10-09)

The queueing model and the measurement plumbing, before the real load sweep.

- `src/mmc.py`: Erlang B/C (stable recursion), mean wait/response, waiting- and response-time
  tails, response-time quantiles, utilisation and capacity helpers, Allen-Cunneen G/G/c and
  M/D/c.
- `src/simulate.py`: FCFS c-server discrete-event simulator used to validate the formulas.
- Target service (httpbin 0.10.2, gunicorn sync workers) and k6 open-model load script.
- Sweep runner and k6 summary parser.
- 69 tests passing.

Not yet present: the measured rate sweep, the model fit, and the knee comparison.
