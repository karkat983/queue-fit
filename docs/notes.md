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

## 2026-10-09: warm-up excluded; k6 sees a shorter service time

`load/test.js` now runs a 10 s warm-up scenario at the target rate before the measured `main`
scenario; only `main` is summarised (k6 sub-metrics `...{scenario:main}`). Because k6 computes a
sub-metric's *rate* over the whole test, the parser derives throughput as main-scenario count /
main duration.

A 20 req/s check run gave p50 = 51.8 ms, about 6 ms below the 57.8 ms measured with sequential
`urllib` requests. k6 reuses keep-alive connections while the sequential script opens a new TCP
connection per request, so the connection set-up was part of the earlier "service time". The fit
therefore estimates μ from low-load k6 runs, which use the same client behaviour as the sweep.

## 2026-10-09: service time for the sweep grid

A 60 s k6 run at 5 req/s (10 s warm-up, 300 measured requests, 0 errors) gave latency
min 51.9 / mean 55.1 / p50 54.8 / p95 57.8 / max 62.4 ms. The sweep grid now uses
**55.1 ms -> mu = 18.1/s per worker, capacity 72.6/s with 4 workers**, and every rate is run
for a 10 s warm-up plus a 60 s measured window.

## 2026-10-09: first full sweep, c = 4, constant service (`results/sweep_c4_constant.csv`)

13 arrival rates (10%-110% of the estimated 72.6/s capacity) x 3 repetitions in shuffled order,
10 s warm-up + 60 s measured per run, k6 open model, `/delay/0.05`. 39 runs, 0 failed requests.
Medians over the three repetitions:

| Target rate (/s) | Throughput | p50 (ms) | p95 (ms) | p95 range over reps | p99 (ms) |
|---|---|---|---|---|---|
| 7.3 | 7.3 | 55.8 | 61.4 | 61.3-62.3 | 61.6 |
| 14.5 | 14.5 | 54.2 | 57.1 | 56.3-61.3 | 59.4 |
| 21.8 | 21.8 | 51.9 | 53.7 | 52.7-54.2 | 55.4 |
| 29.0 | 29.0 | 54.6 | 59.0 | 55.4-59.0 | 59.6 |
| 36.3 | 36.3 | 55.1 | 57.2 | 56.0-57.5 | 57.9 |
| 43.6 | 43.6 | 51.8 | 53.8 | 53.6-54.3 | 54.2 |
| 50.8 | 50.8 | 52.9 | 55.9 | 53.9-56.2 | 56.8 |
| 58.1 | 58.1 | 52.0 | 53.4 | 53.4-53.7 | 54.4 |
| 61.7 | 61.7 | 51.5 | 52.5 | 52.3-52.8 | 54.9 |
| 65.3 | 65.3 | 51.8 | 54.0 | 53.5-56.2 | 76.1 |
| 69.0 | 69.0 | 51.7 | 53.1 | 52.9-53.8 | 59.0 |
| 72.6 | 72.6 | 52.0 | 55.8 | 53.4-75.7 | 92.3 |
| 79.9 | 79.6 | 831.9 | 1158.1 | 1030.7-1266.8 | 1202.5 |

What this shows:

1. **The knee is a cliff.** Latency is flat at ~52-56 ms up to 72.6/s and jumps ~20x at 79.9/s,
   where the queue grows for the whole minute (throughput still matches the offered rate because
   k6 keeps starting requests; latency is what absorbs the overload). With evenly spaced arrivals
   (ca² ~ 0) and near-constant service (cs² = 0.004) there is almost nothing to queue below
   capacity: this is close to a D/D/c system, whose waiting time is zero until rho reaches 1.
   M/M/c would predict a smooth, early rise that this curve does not have.
2. **The service gets faster under load.** p50 falls from ~56 ms at 7/s to ~51.5 ms above 40/s.
   At low rates k6's connections sit idle between requests (and the CPU may clock down), so each
   request pays a little set-up cost. The true capacity is therefore nearer 4 / 0.0518 = 77/s than
   the 72.6/s estimated from the low-load run, and the grid has no point between 72.6 and 79.9,
   exactly where the cliff is. Finer rates near capacity are needed for the knee fit.
3. **The first sign of trouble is the tail.** p99 starts rising at 65-72.6/s (76-92 ms) while p50
   is still flat, and one 72.6/s repetition had p95 = 75.7 ms.
4. k6 reported 49 dropped iterations, all in the overloaded 79.9/s runs (the VU pool ran out
   while requests waited), so the client was not the bottleneck anywhere below capacity.

## 2026-10-09: sweep c = 2, constant service (`results/sweep_c2_constant.csv`)

`WORKERS=2`, same utilisation grid (capacity estimate 2 x 18.1 = 36.3/s), 3 repetitions in
shuffled order, 10 s warm-up + **40 s** measured per run (shorter than c = 4's 60 s to keep the
secondary sweeps under 35 minutes each; at >= 3.6 req/s that is still >= 144 requests per run).
39 runs, 0 failed requests; `classify_run`: 36 ok, 3 overloaded (all at 39.9/s).

| Target (/s) | p50 (ms) | p95 (ms) | p95 range | p99 (ms) | server CPU % |
|---|---|---|---|---|---|
| 3.6 | 54.1 | 57.2 | 56.7-63.4 | 57.4 | 0.4 |
| 7.3 | 54.0 | 57.3 | 56.5-57.7 | 57.8 | 0.8 |
| 10.9 | 53.7 | 56.6 | 56.6-61.2 | 57.9 | 0.9 |
| 14.5 | 53.6 | 56.9 | 56.8-61.1 | 58.0 | 1.2 |
| 18.1 | 53.6 | 56.4 | 56.2-56.6 | 57.0 | 1.3 |
| 21.8 | 52.0 | 53.4 | 52.3-54.0 | 54.7 | 1.6 |
| 25.4 | 52.6 | 54.6 | 54.1-56.5 | 57.2 | 1.4 |
| 29.0 | 53.8 | 56.0 | 55.1-57.0 | 60.0 | 2.2 |
| 30.9 | 53.8 | 55.6 | 55.5-55.8 | 56.2 | 1.7 |
| 32.7 | 54.5 | 57.2 | 55.9-98.3 | 141.1 | 2.7 |
| 34.5 | 54.3 | 56.2 | 56.0-56.2 | 57.1 | 2.0 |
| 36.3 | 54.4 | 56.2 | 56.0-57.6 | 61.7 | 2.0 |
| 39.9 | 736.7 | 1065.7 | 1010.1-1189.7 | 1108.8 | 2.0 |

Same shape as c = 4: flat to 100% of the estimated capacity, then a cliff at 110%. Two new
observations:

- **Server CPU is tiny** (0.4-2.7% of one core, from `docker stats`) and does not track load the
  way utilisation does: the workers are busy *sleeping*. CPU is therefore not a usable proxy for
  rho on this endpoint; worker occupancy (rate x service time / c) is.
- One 32.7/s repetition had p95 = 98 ms and p99 = 141 ms, a transient tail spike well below
  capacity. Shuffled repetitions make such one-offs visible as outliers instead of shifting a
  whole curve.

The client machine's 1-minute load average stayed at 2.2-3.1 on 8 cores, so k6 was never short of
CPU.

## 2026-10-09: sweep c = 8, constant service (`results/sweep_c8_constant.csv`)

`WORKERS=8`, capacity estimate 8 x 18.1 = 145.2/s, 3 repetitions, 10 s warm-up + 40 s measured.
39 runs, 0 failed, 0 dropped; 36 ok, 3 overloaded (all at 159.7/s).

| Target (/s) | p50 (ms) | p95 (ms) | p95 range | p99 (ms) | server CPU % |
|---|---|---|---|---|---|
| 14.5 | 54.7 | 61.3 | 61.2-61.4 | 61.5 | 1.0 |
| 29.0 | 54.3 | 57.3 | 57.1-57.3 | 59.1 | 2.0 |
| 43.6 | 51.4 | 53.0 | 52.9-53.0 | 53.8 | 2.8 |
| 58.1 | 52.1 | 53.4 | 53.4-53.4 | 53.9 | 3.9 |
| 72.6 | 52.0 | 53.7 | 53.7-54.0 | 55.5 | 4.6 |
| 87.1 | 51.3 | 52.7 | 52.6-52.8 | 53.3 | 5.5 |
| 101.6 | 51.4 | 51.8 | 51.7-51.8 | 52.3 | 6.2 |
| 116.2 | 51.4 | 52.3 | 52.2-52.3 | 53.0 | 6.7 |
| 123.4 | 51.4 | 51.8 | 51.7-51.8 | 52.1 | 6.8 |
| 130.7 | 51.2 | 52.2 | 52.2-52.3 | 53.1 | 6.8 |
| 137.9 | 51.3 | 51.7 | 51.6-51.7 | 52.1 | 7.7 |
| 145.2 | 51.3 | 52.0 | 51.9-52.0 | 52.2 | 7.5 |
| 159.7 | 402.5 | 638.8 | 603.5-660.5 | 671.2 | 7.1 |

With eight workers the curve is flatter still: p95 stays within 1 ms of the median from 44/s to
145/s, then jumps 12x. Server CPU rises with load here (1% -> 7.7%) because Flask/WSGI overhead
per request is now spread over more concurrent requests, but it stays far below any CPU limit.

### A fluid check of the overload points

Above capacity a queue grows at (lambda - c mu) per second, so t seconds into a run (warm-up
included) a new request waits about (lambda - c mu) t / (c mu). Averaging that over the measured
window, with the service time seen under load (~51.4 ms, so c mu = c / 0.0514):

| c | lambda | c mu | growth (/s) | run length | wait at end | mean wait over window | measured p50 |
|---|---|---|---|---|---|---|---|
| 4 | 79.9 | 77.8 | 2.1 | 10 + 60 s | ~1.9 s | ~1.1 s | 0.83 s |
| 8 | 159.7 | 155.6 | 4.1 | 10 + 40 s | ~1.3 s | ~0.8 s | 0.40 s |

Both measured medians are below the fluid prediction, by ~25% at c = 4 and ~50% at c = 8. The
simplest explanation is that the service is a little faster under overload than 51.4 ms (a
service time of ~50.5 ms would close most of the gap). Because the excess load is only 2-3% of
capacity, a 1-2% error in the service rate changes the growth rate by half. This is the
knife-edge the fitting phase has to handle: near the knee, latency is extremely sensitive to the
exact service rate, so mu must be estimated from high-load runs, not only from low-load ones.

## 2026-10-09: sanity plots (`scripts/sanity_plots.py`)

- `results/sanity_p95.png`: p95 against estimated utilisation for c = 2, 4, 8 on a log scale.
  All three curves are flat at 52-61 ms from rho = 0.1 to 1.0 and jump 10-20x at rho = 1.1.
  Plotted against utilisation rather than rate, the three server counts collapse onto one
  curve: the knee is a property of utilisation, as queueing theory says.
- `results/sanity_throughput.png`: completed requests/s against offered rate. Every point is on
  the diagonal, including the overloaded ones (k6 keeps starting requests; the backlog shows up
  as latency, not as lost throughput), so no run was limited by the client.
