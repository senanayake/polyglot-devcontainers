from __future__ import annotations

from dataclasses import dataclass, field

import requests
from packaging.version import Version


@dataclass
class EndpointStatus:
    url: str
    status_code: int | None
    healthy: bool
    error: str | None = field(default=None)


def check_endpoint(url: str, *, timeout: int = 5) -> EndpointStatus:
    try:
        response = requests.get(url, timeout=timeout)
        return EndpointStatus(
            url=url,
            status_code=response.status_code,
            healthy=response.status_code < 400,
        )
    except requests.RequestException as exc:
        return EndpointStatus(url=url, status_code=None, healthy=False, error=str(exc))


def check_runtime_version(current: str, minimum: str) -> bool:
    return Version(current) >= Version(minimum)


def summarise(statuses: list[EndpointStatus]) -> dict[str, int]:
    return {
        "total": len(statuses),
        "healthy": sum(1 for s in statuses if s.healthy),
        "unhealthy": sum(1 for s in statuses if not s.healthy),
    }
