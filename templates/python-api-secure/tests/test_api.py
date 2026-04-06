"""Test FastAPI endpoints."""

from fastapi.testclient import TestClient

from python_api_secure_template.main import app

client = TestClient(app)


def test_root() -> None:
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()


def test_health_check() -> None:
    """Test health check endpoint."""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_readiness_check() -> None:
    """Test readiness check endpoint."""
    response = client.get("/api/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_list_items_empty() -> None:
    """Test listing items when empty."""
    response = client.get("/api/items/")
    assert response.status_code == 200
    assert response.json() == []


def test_create_item() -> None:
    """Test creating an item."""
    response = client.post(
        "/api/items/",
        json={"name": "Test Item", "description": "A test item", "price": 10.99, "tax": 1.0},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Item"
    assert data["price"] == 10.99
    assert "id" in data


def test_get_item() -> None:
    """Test getting a specific item."""
    # Create an item first
    create_response = client.post("/api/items/", json={"name": "Test Item", "price": 10.99})
    item_id = create_response.json()["id"]

    # Get the item
    response = client.get(f"/api/items/{item_id}")
    assert response.status_code == 200
    assert response.json()["id"] == item_id


def test_get_nonexistent_item() -> None:
    """Test getting an item that doesn't exist."""
    response = client.get("/api/items/99999")
    assert response.status_code == 404


def test_update_item() -> None:
    """Test updating an item."""
    # Create an item first
    create_response = client.post("/api/items/", json={"name": "Original", "price": 10.0})
    item_id = create_response.json()["id"]

    # Update it
    response = client.put(f"/api/items/{item_id}", json={"name": "Updated", "price": 20.0})
    assert response.status_code == 200
    assert response.json()["name"] == "Updated"
    assert response.json()["price"] == 20.0


def test_delete_item() -> None:
    """Test deleting an item."""
    # Create an item first
    create_response = client.post("/api/items/", json={"name": "To Delete", "price": 5.0})
    item_id = create_response.json()["id"]

    # Delete it
    response = client.delete(f"/api/items/{item_id}")
    assert response.status_code == 204

    # Verify it's gone
    get_response = client.get(f"/api/items/{item_id}")
    assert get_response.status_code == 404


def test_openapi_docs() -> None:
    """Test that OpenAPI docs are available."""
    response = client.get("/api/openapi.json")
    assert response.status_code == 200
    assert "openapi" in response.json()
