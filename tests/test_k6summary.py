import pathlib

import pytest

from src.k6summary import load_summary, parse_summary

FIXTURE = pathlib.Path(__file__).parent / "fixtures" / "k6_summary_rate10.json"


def test_parses_real_k6_summary():
    row = parse_summary(load_summary(FIXTURE))
    assert row["requests"] in (100, 101)               # 10 req/s for 10 s; k6 may fire at t=0 and t=10
    assert row["throughput_rps"] == pytest.approx(10, rel=0.01)
    assert 50 < row["lat_p50_ms"] < row["lat_p95_ms"] < 100


def test_missing_metric_raises():
    with pytest.raises(KeyError):
        parse_summary({"metrics": {}})
