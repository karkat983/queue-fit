# Setup

## Tools and versions (verified 2026-10-09)

| Tool | Version | Install (macOS) |
|------|---------|-----------------|
| k6 | v2.3.0 | `brew install k6` |
| Docker Engine | 29.5.2 (inside Colima) | `brew install colima docker docker-compose` |
| Docker Compose | 5.6.0 | (plugin, see below) |
| Colima VM | aarch64, 4 CPU, 4 GiB RAM | `colima start --cpu 4 --memory 4` |
| Python | 3.12+ for analysis | |
| Host | Apple M3, 8 cores, 24 GB, macOS 15.8.1 | |

Homebrew installs Compose as a CLI plugin; tell Docker where to find it:

```bash
# ~/.docker/config.json
{ "cliPluginsExtraDirs": ["/opt/homebrew/lib/docker/cli-plugins"] }
```

## Target service

The service under test is [httpbin](https://github.com/psf/httpbin) 0.10.2 (Flask 3.1.3,
Werkzeug 3.1.9) served by gunicorn 23.0.0 with `WORKERS` **sync** workers (default 4). A sync
worker handles exactly one request at a time, so the number of workers is a known, true server
count `c` that the M/M/c fit should recover.

The image is built locally from `service/Dockerfile` instead of using the public
`kennethreitz/httpbin` image: that image is amd64-only and runs under CPU emulation on Apple
Silicon, which adds latency noise unrelated to queueing. The local build runs natively
(arm64 here, amd64 elsewhere).

```bash
WORKERS=4 docker compose up -d --build
docker compose logs | grep -c "Booting worker"   # -> 4
curl -s -o /dev/null -w "%{http_code} %{time_total}\n" http://localhost:8080/delay/0.05
```

Three requests to `/delay/0.05` at idle took 56-59 ms (50 ms sleep + ~7 ms overhead).

## Resource isolation caveat

k6 runs on the host and the service runs in the Colima VM on the same machine. The VM is capped
at 4 CPUs so that the load generator has spare cores; client saturation is checked separately
(plan commit 019).
