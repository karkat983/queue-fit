import math

import pytest

from src.mmc import (
    capacity,
    erlang_b,
    erlang_c,
    is_stable,
    mean_response,
    mean_wait,
    rate_at,
    response_quantile,
    response_tail,
    utilisation,
    wait_tail,
)


def test_utilisation():
    assert utilisation(lam=60, mu=20, c=4) == pytest.approx(0.75)


def test_mm1_wait_probability_is_rho():
    # With one server an arrival waits exactly when the server is busy: P(wait) = rho.
    assert erlang_c(1, 0.6) == pytest.approx(0.6)


def test_mm1_response_time_closed_form():
    # M/M/1: E[W] = 1 / (mu - lam)
    assert mean_response(lam=8, mu=10, c=1) == pytest.approx(1 / (10 - 8))


def test_erlang_c_known_value():
    # c = 2, a = 1: a^c/c! * c/(c-a) = 1; sum_{k<2} a^k/k! = 2; C = 1 / 3
    assert erlang_c(2, 1.0) == pytest.approx(1 / 3)


def test_no_load_means_no_wait():
    assert mean_wait(lam=0, mu=20, c=4) == 0
    assert mean_response(lam=0, mu=20, c=4) == pytest.approx(1 / 20)


def test_more_servers_never_wait_longer():
    waits = [mean_wait(lam=30, mu=20, c=c) for c in (2, 3, 4, 8)]
    assert waits == sorted(waits, reverse=True)


def test_wait_grows_sharply_near_saturation():
    # The knee: going from rho 0.5 to 0.95 multiplies queueing delay many times over.
    assert mean_wait(lam=76, mu=20, c=4) > 20 * mean_wait(lam=40, mu=20, c=4)


@pytest.mark.parametrize("lam", [80, 100])
def test_unstable_load_raises(lam):
    with pytest.raises(ValueError, match="unstable"):
        mean_wait(lam=lam, mu=20, c=4)


def erlang_c_exact(c: int, a: int) -> float:
    """Textbook Erlang C in exact rational arithmetic, as a reference for integer loads."""
    from fractions import Fraction
    from math import factorial

    top = Fraction(a ** c, factorial(c)) * Fraction(c, c - a)
    bottom = sum(Fraction(a ** k, factorial(k)) for k in range(c)) + top
    return float(top / bottom)


@pytest.mark.parametrize("c, a", [(1, 0), (2, 1), (8, 6), (64, 60), (64, 32)])
def test_erlang_c_matches_exact_formula(c, a):
    assert erlang_c(c, float(a)) == pytest.approx(erlang_c_exact(c, a), rel=1e-12)


def test_large_c_does_not_overflow():
    # a**c / c! overflows a float for c in the hundreds; the recursion must not.
    p = erlang_c(500, 480.0)
    assert 0 < p < 1
    assert erlang_c(500, 480.0) == pytest.approx(erlang_c_exact(500, 480), rel=1e-9)


def test_erlang_b_known_value():
    # c = 2, a = 1: B = (1/2) / (1 + 1 + 1/2) = 0.2
    assert erlang_b(2, 1.0) == pytest.approx(0.2)


def test_wait_tail_mm1_closed_form():
    # M/M/1: P(Wq > t) = rho * exp(-(mu - lam) t)
    lam, mu, t = 6.0, 10.0, 0.3
    assert wait_tail(t, lam, mu, 1) == pytest.approx(0.6 * math.exp(-(mu - lam) * t))


def test_wait_tail_at_zero_is_probability_of_waiting():
    assert wait_tail(0.0, lam=60, mu=20, c=4) == pytest.approx(erlang_c(4, 3.0))


def test_wait_tail_integrates_to_mean_wait():
    # E[Wq] = integral of P(Wq > t) dt (trapezoid rule; the tail is negligible beyond 2 s)
    lam, mu, c = 60.0, 20.0, 4
    dt, n = 1e-4, 20000
    values = [wait_tail(i * dt, lam, mu, c) for i in range(n + 1)]
    area = (sum(values) - (values[0] + values[-1]) / 2) * dt
    assert area == pytest.approx(mean_wait(lam, mu, c), rel=1e-3)


def test_response_quantile_mm1_closed_form():
    # M/M/1: T ~ Exp(mu - lam), so the p-quantile is -ln(1 - p) / (mu - lam)
    lam, mu = 6.0, 10.0
    assert response_quantile(0.95, lam, mu, 1) == pytest.approx(-math.log(0.05) / (mu - lam), rel=1e-9)


def test_response_quantile_inverts_the_tail():
    lam, mu, c = 70.0, 20.0, 4
    t95 = response_quantile(0.95, lam, mu, c)
    assert response_tail(t95, lam, mu, c) == pytest.approx(0.05, rel=1e-9)


def test_response_tail_handles_the_degenerate_rate():
    # c*mu - lam == mu  ->  the closed form's 0/0 case
    lam, mu, c = 60.0, 20.0, 4
    near = response_tail(0.1, lam * (1 + 1e-9), mu, c)
    assert response_tail(0.1, lam, mu, c) == pytest.approx(near, rel=1e-6)


def test_p95_rises_steeply_near_saturation():
    mu, c = 20.0, 4
    p95 = [response_quantile(0.95, rho * c * mu, mu, c) for rho in (0.5, 0.8, 0.95)]
    assert p95[0] < p95[1] < p95[2]
    assert p95[2] > 4 * p95[0]


def test_capacity_and_rate_at():
    assert capacity(mu=17.7, c=4) == pytest.approx(70.8)
    assert rate_at(0.5, mu=20, c=4) == pytest.approx(40)
    assert utilisation(rate_at(0.83, mu=20, c=4), mu=20, c=4) == pytest.approx(0.83)


@pytest.mark.parametrize("lam, mu, c, stable", [
    (79.9, 20, 4, True), (80, 20, 4, False), (0, 20, 4, True), (-1, 20, 4, False), (10, 0, 4, False),
    (10, 20, 0, False),
])
def test_is_stable(lam, mu, c, stable):
    assert is_stable(lam, mu, c) is stable


@pytest.mark.parametrize("lam, mu, c", [(-1, 20, 4), (10, 0, 4), (10, 20, 0)])
def test_invalid_parameters_raise(lam, mu, c):
    with pytest.raises(ValueError, match="need"):
        mean_wait(lam, mu, c)


@pytest.mark.parametrize("fn", [
    lambda lam: erlang_c(4, lam / 20),
    lambda lam: mean_wait(lam, 20, 4),
    lambda lam: mean_response(lam, 20, 4),
    lambda lam: wait_tail(0.1, lam, 20, 4),
    lambda lam: response_tail(0.1, lam, 20, 4),
    lambda lam: response_quantile(0.95, lam, 20, 4),
])
@pytest.mark.parametrize("lam", [80.0, 120.0])
def test_every_formula_rejects_rho_at_or_above_one(fn, lam):
    with pytest.raises(ValueError, match="unstable"):
        fn(lam)
