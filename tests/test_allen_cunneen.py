import pytest

from src.mmc import (
    allen_cunneen_response,
    allen_cunneen_wait,
    mdc_response,
    mdc_wait,
    mean_response,
    mean_wait,
)
from src.simulate import constant, simulate


@pytest.mark.parametrize("lam, mu, c", [(6.0, 10.0, 1), (60.0, 20.0, 4), (150.0, 20.0, 8)])
def test_reduces_to_mmc_for_exponential_arrivals_and_service(lam, mu, c):
    assert allen_cunneen_wait(lam, mu, c, ca2=1.0, cs2=1.0) == pytest.approx(mean_wait(lam, mu, c))
    assert allen_cunneen_response(lam, mu, c) == pytest.approx(mean_response(lam, mu, c))


def test_scales_linearly_with_variability():
    base = mean_wait(60.0, 20.0, 4)
    assert allen_cunneen_wait(60.0, 20.0, 4, ca2=1.0, cs2=0.0) == pytest.approx(base / 2)
    assert allen_cunneen_wait(60.0, 20.0, 4, ca2=1.0, cs2=3.0) == pytest.approx(2 * base)


def test_negative_variability_rejected():
    with pytest.raises(ValueError):
        allen_cunneen_wait(60.0, 20.0, 4, cs2=-0.1)


def test_md1_is_exact():
    lam, mu = 7.0, 10.0
    rho = lam / mu
    assert mdc_wait(lam, mu, 1) == pytest.approx(rho / (2 * mu * (1 - rho)))


@pytest.mark.parametrize("rho", [0.6, 0.8, 0.9])
def test_mdc_close_to_simulation(rho):
    mu, c = 20.0, 4
    lam = rho * c * mu
    sim = simulate(lam, c, constant(mu), n_jobs=300_000, seed=11)
    # Allen-Cunneen is an approximation for c > 1: within 10% on the queueing delay,
    # and much closer on total response time, which is what the fit uses.
    assert sim.mean_wait() == pytest.approx(mdc_wait(lam, mu, c), rel=0.10)
    assert sim.mean_response() == pytest.approx(mdc_response(lam, mu, c), rel=0.03)
