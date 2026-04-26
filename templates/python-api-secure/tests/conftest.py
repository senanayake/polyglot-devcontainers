from collections.abc import Iterator

import pytest

from python_api_secure_template.routers import items


@pytest.fixture(autouse=True)
def reset_items_db() -> Iterator[None]:
    """Keep the demo API tests independent and order-insensitive."""
    items.items_db.clear()
    items.next_id = 1
    yield
    items.items_db.clear()
    items.next_id = 1
