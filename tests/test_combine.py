import pandas as pd

from src.combine import load_runs, summarise


def write(path, rows):
    pd.DataFrame(rows).to_csv(path, index=False)
    return str(path)


def run(rate, rep, p95, p50=52.0, workers=4, dropped=0):
    return {"workers": workers, "service": "constant", "target_rps": rate, "rep": rep, "requests": 100,
            "throughput_rps": rate, "lat_mean_ms": p50, "lat_p50_ms": p50, "lat_p95_ms": p95,
            "lat_p99_ms": p95, "dropped": dropped, "error_rate": 0}


def test_repetitions_collapse_to_median_and_range(tmp_path):
    a = write(tmp_path / "sweep_a.csv", [run(10, 1, 55), run(10, 2, 99), run(10, 3, 56)])
    table = summarise(load_runs([a], service_time_s=0.05))
    (row,) = table.to_dict("records")
    assert row["lat_p95_ms"] == 56 and row["p95_min_ms"] == 55 and row["p95_max_ms"] == 99
    assert row["reps"] == 3 and row["requests"] == 300


def test_files_with_different_columns_combine_and_overload_is_flagged(tmp_path):
    old = write(tmp_path / "sweep_old.csv", [run(80, 1, 1200, p50=900, dropped=5)])
    new_rows = [dict(run(20, 1, 55, workers=2), server_cpu_pct=1.5)]
    new = write(tmp_path / "sweep_new.csv", new_rows)
    table = summarise(load_runs([old, new], service_time_s=0.05)).set_index("workers")
    assert table.loc[4, "overloaded_reps"] == 1
    assert table.loc[2, "overloaded_reps"] == 0
    assert table.loc[2, "rho_est"] == 0.5
