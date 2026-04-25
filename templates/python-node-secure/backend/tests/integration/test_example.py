import pytest


@pytest.mark.integration
def test_integration_example() -> None:
    assert {"status": "ok"}["status"] == "ok"
