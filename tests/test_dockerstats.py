import json

import pytest

from src.dockerstats import Sampler, parse_bytes, parse_percent, summarise

LINE = json.dumps({"Name": "queue-fit-httpbin-1", "CPUPerc": "6.26%", "MemUsage": "101.9MiB / 3.813GiB"})


def test_sampler_records_readings_and_writes_jsonl(tmp_path):
    path = tmp_path / "run.docker.jsonl"
    with Sampler("c", path, interval=0.01, sample=lambda c: LINE) as s:
        while len(s.readings) < 3:
            pass
    lines = [json.loads(x) for x in path.read_text().splitlines()]
    assert len(lines) >= 3
    assert lines[0]["stats"]["CPUPerc"] == "6.26%"
    assert lines == sorted(lines, key=lambda r: r["t_s"])


def test_sampler_survives_a_failing_sample(tmp_path):
    def flaky(container):
        raise IndexError("no output")

    with Sampler("c", tmp_path / "x.jsonl", interval=0.01, sample=flaky):
        pass
    assert (tmp_path / "x.jsonl").read_text() == ""



@pytest.mark.parametrize("text, value", [("6.26%", 6.26), ("0.00%", 0.0), ("312.5%", 312.5)])
def test_parse_percent(text, value):
    assert parse_percent(text) == value


@pytest.mark.parametrize("text, value", [
    ("101.9MiB", int(101.9 * 1024**2)), ("1.5GiB", int(1.5 * 1024**3)), ("512KiB", 512 * 1024),
    ("12kB", 12_000), ("0B", 0),
])
def test_parse_bytes(text, value):
    assert parse_bytes(text) == value


def test_parse_bytes_rejects_garbage():
    with pytest.raises(ValueError):
        parse_bytes("lots")


def test_summarise_skips_warmup_and_averages_cpu():
    def reading(t, cpu, mem):
        return {"t_s": t, "stats": {"CPUPerc": cpu, "MemUsage": f"{mem} / 3.8GiB"}}

    readings = [reading(0, "90%", "100MiB"), reading(12, "10%", "110MiB"), reading(14, "30%", "120MiB")]
    s = summarise(readings, skip_s=10)
    assert s == {"server_cpu_pct": 20.0, "server_mem_mb": 120.0, "cpu_samples": 2}


def test_summarise_with_no_samples():
    assert summarise([], skip_s=0)["server_cpu_pct"] is None
