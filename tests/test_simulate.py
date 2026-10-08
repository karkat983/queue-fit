import numpy as np
import pytest

from src.mmc import mean_response, mean_wait, response_quantile
from src.simulate import constant, exponential, simulate


@pytest.mark.parametrize("lam, mu, c", [(6.0, 10.0, 1), (60.0, 20.0, 4), (70.0, 20.0, 4), (150.0, 20.0, 8)])
def test_simulated_mean_wait_matches_erlang_c(lam, mu, c):
    # Near saturation successive waits are strongly correlated, so a 300k-job run still has a
    # few percent of sampling error; the tolerances reflect that, not model error.
    sim = simulate(lam, c, exponential(mu), n_jobs=300_000, seed=1)
    assert sim.mean_wait() == pytest.approx(mean_wait(lam, mu, c), rel=0.08)
    assert sim.mean_response() == pytest.approx(mean_response(lam, mu, c), rel=0.04)


def test_simulated_p95_matches_formula():
    sim = simulate(60.0, 4, exponential(20.0), n_jobs=300_000, seed=2)
    assert sim.quantile(0.95) == pytest.approx(response_quantile(0.95, 60.0, 20.0, 4), rel=0.02)


def test_constant_service_md1_matches_pollaczek_khinchine():
    # M/D/1: E[Wq] = rho / (2 mu (1 - rho))
    lam, mu = 7.0, 10.0
    rho = lam / mu
    sim = simulate(lam, 1, constant(mu), n_jobs=300_000, seed=3)
    assert sim.mean_wait() == pytest.approx(rho / (2 * mu * (1 - rho)), rel=0.05)


def test_no_waiting_when_servers_outnumber_arrivals():
    gaps = np.full(1000, 1.0)                     # one arrival per second, service 0.5 s
    sim = simulate(1.0, 1, constant(2.0), interarrivals=gaps, warmup=0)
    assert sim.mean_wait() == 0
    assert sim.mean_response() == pytest.approx(0.5)


def test_same_seed_same_result():
    a = simulate(60.0, 4, exponential(20.0), n_jobs=20_000, seed=7)
    b = simulate(60.0, 4, exponential(20.0), n_jobs=20_000, seed=7)
    assert np.array_equal(a.waits, b.waits)
