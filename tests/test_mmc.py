import pytest

from src.mmc import erlang_c, mean_response, mean_wait, utilisation


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
