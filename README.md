# queue-fit

> Status: **in progress.** Sections marked *planned* are not built yet.

## Problem
Load tests show latency staying flat and then shooting up, but the point where that happens is usually found by trial and error rather than predicted. This matters because a model that predicts the latency knee from a few low-load measurements lets you plan capacity before users hit it. See Harchol-Balter 2013, *Performance Modeling and Design of Computer Systems*, ch. 14 (M/M/k).

## Approach
*Planned.* Load-test a containerised open-source HTTP service (httpbin under gunicorn with a known number of workers) at a sweep of arrival rates with k6, then fit an M/M/c queueing model to the measured latency and compare its predicted knee with the measured one.

## Results
*Planned.* No numbers yet.

| Metric | Value |
|--------|-------|
| Fitted service rate μ | — |
| Fitted servers c (true: 4) | — |
| Predicted vs measured knee | — |

## Run it
Requires Docker and k6.
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
WORKERS=4 docker compose up -d                  # httpbin with 4 sync workers on :8080
k6 run -e RATE=40 load/test.js                  # one load level -> results/raw/rate40.json
pytest                                          # M/M/c model tests
```
The rate sweep, model fit and plots are *planned*. The load test has not been run yet.

## What I learned
*Planned.*

## Notes
No external data; all measurements come from load tests run locally against open-source software (httpbin, k6). Not affiliated with any employer. Built October 2026.

## Changelog
- Day 1: project scaffold and changelog.
