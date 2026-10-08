import pathlib

import pytest

from src.k6summary import FIELDS, load_summary, parse_summary

FIXTURE = pathlib.Path(__file__).parent / "fixtures" / "k6_summary_rate10.json"


def test_parses_real_k6_summary():
    row = parse_summary(load_summary(FIXTURE))
    assert row["requests"] in (100, 101)               # 10 req/s for 10 s; k6 may fire at t=0 and t=10
    assert row["throughput_rps"] == pytest.approx(10, rel=0.01)
    assert 50 < row["lat_p50_ms"] < row["lat_p95_ms"] < 100


def test_missing_metric_raises():
    with pytest.raises(KeyError):
        parse_summary({"metrics": {}})


def test_all_fields_present_and_ordered():
    row = parse_summary(load_summary(FIXTURE))
    assert list(row) == FIELDS
    assert row["lat_min_ms"] <= row["lat_p50_ms"] <= row["lat_p90_ms"] <= row["lat_p95_ms"] \
        <= row["lat_p99_ms"] <= row["lat_max_ms"]
    assert row["failed"] == 0 and row["dropped"] == 0


def test_dropped_and_failed_are_read_when_present():
    summary = load_summary(FIXTURE)
    summary["metrics"]["dropped_iterations"] = {"type": "counter", "values": {"count": 7, "rate": 0.7}}
    summary["metrics"]["http_req_failed"]["values"].update({"passes": 3, "rate": 0.03})
    row = parse_summary(summary)
    assert row["dropped"] == 7
    assert row["failed"] == 3
    assert row["error_rate"] == pytest.approx(0.03)
