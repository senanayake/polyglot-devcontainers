import pytest
from fastapi.testclient import TestClient
from httpx import Response
from pytest_bdd import given, scenarios, then, when

from python_api_secure_template.main import app

pytestmark = pytest.mark.acceptance

scenarios("api-health.feature")


@given("an API test client", target_fixture="client")
def given_client() -> TestClient:
    return TestClient(app)


@when("the health endpoint is requested", target_fixture="response")
def when_health_is_requested(client: TestClient) -> Response:
    return client.get("/api/health")


@then("the response status code is 200")
def then_status_code_is_200(response: Response) -> None:
    assert response.status_code == 200


@then('the response payload contains the status "healthy"')
def then_payload_contains_status(response: Response) -> None:
    assert response.json() == {"status": "healthy"}
