import pytest
from fastapi.testclient import TestClient
from hypothesis import given
from hypothesis import strategies as st

from python_api_secure_template.main import app

pytestmark = pytest.mark.property


@given(
    name=st.text(
        alphabet=st.characters(whitelist_categories=("Ll", "Lu", "Nd")),
        min_size=1,
        max_size=20,
    ),
    price=st.integers(min_value=0, max_value=10_000),
)
def test_create_item_round_trip(name: str, price: int) -> None:
    client = TestClient(app)
    response = client.post("/api/items/", json={"name": name, "price": price})
    assert response.status_code == 201
    payload = response.json()
    assert payload["name"] == name
    assert payload["price"] == price
