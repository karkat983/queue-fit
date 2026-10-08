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
