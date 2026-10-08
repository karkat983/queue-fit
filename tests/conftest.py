import pathlib
import urllib.request

import pytest

FIXTURES = pathlib.Path(__file__).parent / "fixtures"


@pytest.fixture
def fixtures_dir() -> pathlib.Path:
    return FIXTURES


def service_up(url: str = "http://localhost:8080/get") -> bool:
    try:
        with urllib.request.urlopen(url, timeout=1) as resp:
            return resp.status == 200
    except OSError:
        return False


def pytest_collection_modifyitems(config, items):
    if service_up():
        return
    skip = pytest.mark.skip(reason="target service not running (make up)")
    for item in items:
        if "service" in item.keywords:
            item.add_marker(skip)
