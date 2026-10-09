import importlib.util
import pathlib

import pytest

spec = importlib.util.spec_from_file_location(
    "sweep", pathlib.Path(__file__).resolve().parent.parent / "scripts" / "sweep.py"
)
sweep = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sweep)


@pytest.mark.parametrize("text, secs", [("60s", 60), ("2m", 120), ("1m30s", 90), ("500ms", 0.5)])
def test_seconds(text, secs):
    assert sweep.seconds(text) == secs


def test_bad_duration():
    with pytest.raises(ValueError):
        sweep.seconds("soon")


def test_run_order_covers_every_rate_each_rep_in_shuffled_order():
    rates = [10.0, 20.0, 30.0, 40.0, 50.0]
    order = sweep.run_order(rates, reps=3, seed=1)
    assert len(order) == 15
    for rep in (1, 2, 3):
        assert sorted(r for k, r in order if k == rep) == rates
    per_rep = [[r for k, r in order if k == rep] for rep in (1, 2, 3)]
    assert per_rep[0] != per_rep[1] or per_rep[1] != per_rep[2]     # not the same order every time


def test_run_order_is_reproducible():
    assert sweep.run_order([1.0, 2.0, 3.0], 2, seed=5) == sweep.run_order([1.0, 2.0, 3.0], 2, seed=5)


def test_append_row_refuses_a_file_with_other_columns(tmp_path):
    path = tmp_path / "runs.csv"
    path.write_text("old,columns\n1,2\n")
    with pytest.raises(SystemExit, match="different columns"):
        sweep.append_row(path, {})


def test_append_row_writes_header_once(tmp_path):
    path = tmp_path / "runs.csv"
    row = dict.fromkeys(sweep.RUN_FIELDS, 1)
    sweep.append_row(path, row)
    sweep.append_row(path, row)
    lines = path.read_text().splitlines()
    assert len(lines) == 3 and lines[0].split(",") == sweep.RUN_FIELDS


def test_k6_command_passes_timeout_and_service():
    cmd = sweep.k6_command("http://x", 12.5, "60s", "10s", pathlib.Path("o.json"), "exponential", "5s")
    env = [cmd[i + 1] for i, part in enumerate(cmd) if part == "-e"]
    assert "TIMEOUT=5s" in env and "SERVICE=exponential" in env and "RATE=12.5" in env
