import importlib.util
import pathlib

import numpy as np
import pytest

spec = importlib.util.spec_from_file_location(
    "poisson_load", pathlib.Path(__file__).resolve().parent.parent / "scripts" / "poisson_load.py"
)
poisson_load = importlib.util.module_from_spec(spec)
spec.loader.exec_module(poisson_load)


def test_schedule_has_poisson_rate_and_exponential_gaps():
    times = poisson_load.schedule(rate=50, duration=2000, seed=3)
    assert len(times) / 2000 == pytest.approx(50, rel=0.02)
    gaps = np.diff(times)
    assert gaps.var() / gaps.mean() ** 2 == pytest.approx(1.0, abs=0.05)     # exponential: SCV 1
    assert times.max() < 2000


def test_delay_modes():
    assert set(poisson_load.delays(5, "constant", 0.05, 0)) == {0.05}
    exp = poisson_load.delays(100_000, "exponential", 0.05, 0)
    assert exp.mean() == pytest.approx(0.05, rel=0.02)
    assert exp.max() <= 10.0
