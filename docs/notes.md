# Working notes

## 2026-10-09: first k6 run (5 req/s, 30 s, `/delay/0.05`, 4 workers)

```
k6 run -e RATE=5 -e DURATION=30s -e OUT=results/raw/rate5.json load/test.js
rate=5/s p50=55.7ms p95=61.5ms
```

| Metric | Value |
|--------|-------|
| requests | 150 (4.9999/s) |
| failed | 0 |
| latency min / p50 / mean | 51.6 / 55.7 / 56.4 ms |
| latency p90 / p95 / p99 / max | 61.1 / 61.5 / 61.8 / 61.9 ms |
| VUs allocated | 10 (none dropped) |

At rho = 5 / (4 x ~18/s) ~ 0.07 there is essentially no queueing, so this run measures service
time: 50 ms of sleep plus ~6 ms of HTTP, WSGI and VM-network overhead. The spread is tight
(min 51.6, max 61.9 ms): the sleep endpoint gives near-deterministic service, which matters for
the model choice (M/D/c rather than M/M/c; see plan).

### Summary JSON shape (what the parser must read)

- `metrics.http_req_duration.values`: `avg`, `min`, `med`, `max`, `p(90)`, `p(95)`, `p(99)`
  in milliseconds (set by `summaryTrendStats` in `load/test.js`).
- `metrics.http_reqs.values`: `count`, `rate` (completed requests per second).
- `metrics.http_req_failed.values`: `passes` = failed requests, `rate` = failure share.
- `metrics.dropped_iterations` appears **only when** k6 had to drop arrivals (VU pool
  exhausted); absent means zero.
- `state.testRunDurationMs`: wall-clock test duration.

## 2026-10-09: service time at zero load (`scripts/service_time.py`)

100 sequential requests to `/delay/0.05` (one at a time, 50 ms pause between them, after 5
warm-up requests), so no request ever waited for a worker:

| Statistic | Latency |
|-----------|---------|
| mean | 57.80 ms |
| min | 52.12 ms |
| median | 57.20 ms |
| max | 71.69 ms |

Raw samples: `results/service_time.csv`. The 50 ms sleep plus ~7.8 ms of overhead (HTTP,
Flask routing, the Colima VM's network path) gives a mean service time of ~57.8 ms, i.e.
**mu ~ 17.3 requests/s per worker** and a capacity of ~69 requests/s with 4 workers.

### Variability of the service time

From the same 100 samples: standard deviation 3.63 ms, coefficient of variation 0.063,
**squared CV cs² = 0.004** (`src/variability.py`). Exponential service would give cs² = 1, so
the constant-delay endpoint is effectively deterministic: an M/M/c model would overstate the
queueing delay roughly twofold (Allen-Cunneen factor (ca² + cs²)/2), and M/D/c is the
better-matched model for this mode. The exponential mode (client-drawn delays) is what tests
M/M/c itself.
