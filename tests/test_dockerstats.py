import json

from src.dockerstats import Sampler

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
