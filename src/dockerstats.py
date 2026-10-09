"""Sample the target container's CPU and memory with `docker stats` while a load run is going.

The sampler runs in a background thread and keeps every raw `docker stats` JSON line with the
time it was taken, so a run's server-side CPU can be compared with the utilisation the queueing
model implies.
"""
import json
import pathlib
import subprocess
import threading
import time


def sample_raw(container: str) -> str:
    """One `docker stats --no-stream` reading for the container, as its JSON line."""
    return subprocess.run(
        ["docker", "stats", "--no-stream", "--format", "{{json .}}", container],
        capture_output=True, text=True, check=True,
    ).stdout.strip().splitlines()[0]


class Sampler:
    """`with Sampler(container, path):` samples every `interval` seconds until the block exits,
    then writes the readings as JSON lines: {"t_s": seconds since start, "stats": {...}}."""

    def __init__(self, container: str, path: pathlib.Path | str, interval: float = 2.0, sample=sample_raw):
        self.container = container
        self.path = pathlib.Path(path)
        self.interval = interval
        self.sample = sample
        self.readings: list[dict] = []
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def _run(self) -> None:
        t0 = time.monotonic()
        while not self._stop.is_set():
            try:
                line = self.sample(self.container)
                self.readings.append({"t_s": round(time.monotonic() - t0, 2), "stats": json.loads(line)})
            except (subprocess.CalledProcessError, IndexError, json.JSONDecodeError):
                pass                                    # a missed sample is not worth failing a run
            self._stop.wait(self.interval)

    def __enter__(self):
        self._thread.start()
        return self

    def __exit__(self, *exc):
        self._stop.set()
        self._thread.join()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text("".join(json.dumps(r) + "\n" for r in self.readings))
