import pandas as pd
import pytest

from src.runs import classify_run

BASE = 55.0


@pytest.mark.parametrize("row, rho, label", [
    ({"lat_p50_ms": 52, "dropped": 0, "error_rate": 0}, 0.8, "ok"),
    ({"lat_p50_ms": 832, "dropped": 16, "error_rate": 0}, 1.03, "overloaded"),
    ({"lat_p50_ms": 300, "dropped": 0, "error_rate": 0}, 0.99, "overloaded"),
    ({"lat_p50_ms": 60, "dropped": 0, "error_rate": 0.05}, 0.5, "overloaded"),
    ({"lat_p50_ms": 53, "dropped": 40, "error_rate": 0}, 0.5, "client_limited"),
])
def test_classify(row, rho, label):
    assert classify_run(row, BASE, rho) == label


def test_c4_sweep_only_the_110_percent_rate_is_overloaded():
    df = pd.read_csv("results/sweep_c4_constant.csv")
    labels = {r.target_rps: classify_run(r._asdict(), BASE) for r in df.itertuples()}
    assert {rate for rate, label in labels.items() if label != "ok"} == {79.9}
