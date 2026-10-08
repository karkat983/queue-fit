import pytest

from src.grid import rate_grid


def test_grid_scales_capacity():
    # 50 ms service, 4 workers -> capacity 80/s
    assert rate_grid(0.05, 4, [0.1, 0.5, 1.0, 1.1]) == [8.0, 40.0, 80.0, 88.0]


def test_grid_from_measured_service_time():
    rates = rate_grid(0.0578, 4, [0.5, 1.0])
    assert rates[1] == pytest.approx(69.2, abs=0.05)
    assert rates[0] == pytest.approx(34.6, abs=0.05)
