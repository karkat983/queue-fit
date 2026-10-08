import numpy as np
import pytest

from src.variability import scv


def test_constant_samples_have_zero_scv():
    assert scv([0.05] * 10) == 0


def test_exponential_samples_have_scv_near_one():
    rng = np.random.default_rng(0)
    assert scv(list(rng.exponential(0.05, 100_000))) == pytest.approx(1.0, abs=0.03)


def test_needs_two_samples():
    with pytest.raises(ValueError):
        scv([1.0])
