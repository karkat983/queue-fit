import json
import urllib.request

import pytest


@pytest.mark.service
def test_delay_endpoint_answers():
    with urllib.request.urlopen("http://localhost:8080/delay/0.05", timeout=5) as resp:
        body = json.load(resp)
    assert resp.status == 200
    assert body["url"].endswith("/delay/0.05")
