"""Items CRUD endpoints - example resource."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()


class Item(BaseModel):
    """Item model."""

    id: int
    name: str
    description: str | None = None
    price: float
    tax: float | None = None


class ItemCreate(BaseModel):
    """Item creation model."""

    name: str
    description: str | None = None
    price: float
    tax: float | None = None


# In-memory storage for demo purposes
items_db: dict[int, Item] = {}
next_id = 1


@router.get("/")
async def list_items() -> list[Item]:
    """List all items."""
    return list(items_db.values())


@router.get("/{item_id}")
async def get_item(item_id: int) -> Item:
    """Get a specific item by ID."""
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail="Item not found")
    return items_db[item_id]


@router.post("/", status_code=201)
async def create_item(item: ItemCreate) -> Item:
    """Create a new item."""
    global next_id
    new_item = Item(id=next_id, **item.model_dump())
    items_db[next_id] = new_item
    next_id += 1
    return new_item


@router.put("/{item_id}")
async def update_item(item_id: int, item: ItemCreate) -> Item:
    """Update an existing item."""
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail="Item not found")
    updated_item = Item(id=item_id, **item.model_dump())
    items_db[item_id] = updated_item
    return updated_item


@router.delete("/{item_id}", status_code=204)
async def delete_item(item_id: int) -> None:
    """Delete an item."""
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail="Item not found")
    del items_db[item_id]
