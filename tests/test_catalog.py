"""
Test suite for Catalog Service
Run: pytest tests/ -v
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

os.environ["AUTH_REQUIRED"] = "false"
os.environ["ENVIRONMENT"] = "test"

from src.main import app
from src.database import Base, get_db

TEST_DB = "sqlite+aiosqlite:///./test.db"
test_engine = create_async_engine(TEST_DB, echo=False)
TestSession = sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_db():
    async with TestSession() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_health_check(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["service"] == "catalog-service"


@pytest.mark.asyncio
async def test_list_restaurants_empty(client):
    resp = await client.get("/api/v1/restaurants")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0
    assert data["items"] == []


@pytest.mark.asyncio
async def test_create_and_get_restaurant(client):
    payload = {
        "name": "Test Pizza Place",
        "address": "123 Test Street, Colombo",
        "cuisine_type": "Italian",
        "delivery_time_minutes": 25,
    }
    resp = await client.post("/api/v1/restaurants", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Test Pizza Place"
    assert data["cuisine_type"] == "Italian"

    restaurant_id = data["id"]
    resp2 = await client.get(f"/api/v1/restaurants/{restaurant_id}")
    assert resp2.status_code == 200
    assert resp2.json()["id"] == restaurant_id


@pytest.mark.asyncio
async def test_create_menu_item(client):
    # Create restaurant first
    r = await client.post("/api/v1/restaurants", json={
        "name": "Burger Spot", "address": "45 Main Rd, Kandy"
    })
    restaurant_id = r.json()["id"]

    item_payload = {
        "restaurant_id": restaurant_id,
        "name": "Classic Burger",
        "price": 9.99,
        "category": "Burgers",
        "is_vegetarian": False,
        "calories": 650,
    }
    resp = await client.post("/api/v1/menu-items", json=item_payload)
    assert resp.status_code == 201
    item = resp.json()
    assert item["name"] == "Classic Burger"
    assert item["price"] == 9.99


@pytest.mark.asyncio
async def test_bulk_lookup_endpoint(client):
    """Tests the inter-service endpoint used by Order Service"""
    r = await client.post("/api/v1/restaurants", json={
        "name": "Sushi World", "address": "77 Bay Ave, Colombo"
    })
    rid = r.json()["id"]

    item1 = (await client.post("/api/v1/menu-items", json={
        "restaurant_id": rid, "name": "Salmon Roll", "price": 14.99, "category": "Sushi"
    })).json()
    item2 = (await client.post("/api/v1/menu-items", json={
        "restaurant_id": rid, "name": "Tuna Nigiri", "price": 11.50, "category": "Sushi"
    })).json()

    resp = await client.post("/api/v1/menu-items/bulk-lookup", json={
        "item_ids": [item1["id"], item2["id"], "non-existent-id"]
    })
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == 2
    assert "non-existent-id" in data["unavailable_ids"]


@pytest.mark.asyncio
async def test_restaurant_not_found(client):
    resp = await client.get("/api/v1/restaurants/does-not-exist")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_menu_item(client):
    r = await client.post("/api/v1/restaurants", json={
        "name": "Cafe Fresh", "address": "10 Green St, Colombo"
    })
    rid = r.json()["id"]
    item = (await client.post("/api/v1/menu-items", json={
        "restaurant_id": rid, "name": "Salad", "price": 7.99
    })).json()

    resp = await client.put(f"/api/v1/menu-items/{item['id']}", json={"price": 8.99})
    assert resp.status_code == 200
    assert resp.json()["price"] == 8.99
