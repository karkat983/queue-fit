import pytest

from src.mmc import allen_cunneen_response, allen_cunneen_wait, mean_response, mean_wait


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
