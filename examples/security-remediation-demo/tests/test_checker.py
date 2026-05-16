from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from health_monitor.checker import EndpointStatus, check_endpoint, check_runtime_version, summarise


def _mock_response(status_code: int) -> MagicMock:
    mock = MagicMock()
    mock.status_code = status_code
    return mock


def test_healthy_endpoint() -> None:
    with patch("health_monitor.checker.requests.get", return_value=_mock_response(200)):
        status = check_endpoint("http://example.com/health")
    assert status.healthy
    assert status.status_code == 200
    assert status.error is None


def test_server_error_endpoint() -> None:
    with patch("health_monitor.checker.requests.get", return_value=_mock_response(503)):
        status = check_endpoint("http://example.com/health")
    assert not status.healthy
    assert status.status_code == 503


def test_connection_error() -> None:
    import requests as req

    with patch("health_monitor.checker.requests.get", side_effect=req.ConnectionError("refused")):
        status = check_endpoint("http://unreachable.example.com/")
    assert not status.healthy
    assert status.status_code is None
    assert "refused" in (status.error or "")


@pytest.mark.parametrize(
    "current,minimum,expected",
    [
        ("3.12.0", "3.11.0", True),
        ("3.11.0", "3.11.0", True),
        ("3.10.9", "3.11.0", False),
        ("2.0.0", "1.9.9", True),
    ],
)
def test_check_runtime_version(current: str, minimum: str, expected: bool) -> None:
    assert check_runtime_version(current, minimum) is expected


def test_summarise() -> None:
    statuses = [
        EndpointStatus(url="http://a", status_code=200, healthy=True),
        EndpointStatus(url="http://b", status_code=500, healthy=False),
        EndpointStatus(url="http://c", status_code=200, healthy=True),
    ]
    result = summarise(statuses)
    assert result == {"total": 3, "healthy": 2, "unhealthy": 1}
