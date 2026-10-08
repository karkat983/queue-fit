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
