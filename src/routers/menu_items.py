"""
Menu Items endpoints.
Includes /bulk-lookup used by the Order Service for inter-service communication.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
import math

from ..database import get_db
from ..models import MenuItem, Restaurant
from ..schemas import (
    MenuItemCreate, MenuItemUpdate, MenuItemResponse,
    PaginatedResponse, BulkItemsRequest, BulkItemsResponse
)
from ..middleware import get_current_user

router = APIRouter()


@router.get("", response_model=PaginatedResponse, summary="List Menu Items")
async def list_menu_items(
    restaurant_id: Optional[str] = None,
    category: Optional[str] = None,
    is_available: bool = True,
    is_vegetarian: Optional[bool] = None,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Public endpoint. Filter menu items by restaurant, category, or dietary preference."""
    query = select(MenuItem).where(MenuItem.is_available == is_available)
    if restaurant_id:
        query = query.where(MenuItem.restaurant_id == restaurant_id)
    if category:
        query = query.where(MenuItem.category.ilike(f"%{category}%"))
    if is_vegetarian is not None:
        query = query.where(MenuItem.is_vegetarian == is_vegetarian)

    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar()

    query = query.offset((page - 1) * size).limit(size)
    result = await db.execute(query)
    items = result.scalars().all()

    return PaginatedResponse(
        items=[MenuItemResponse.model_validate(i) for i in items],
        total=total,
        page=page,
        size=size,
        pages=math.ceil(total / size) if total else 0,
    )


@router.get("/{item_id}", response_model=MenuItemResponse, summary="Get Menu Item")
async def get_menu_item(item_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MenuItem).where(MenuItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Menu item not found")
    return item


# ── Inter-Service Communication Endpoint ─────────────────────────────────────

@router.post("/bulk-lookup", response_model=BulkItemsResponse, summary="Bulk Item Lookup (Order Service)")
async def bulk_item_lookup(
    payload: BulkItemsRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Internal endpoint called by the ORDER SERVICE when a user places an order.
    Validates that all requested item IDs exist and are currently available.
    Returns item details (including price) for order total calculation.

    This is the primary inter-service communication point.
    Called by: Order Management Service
    """
    result = await db.execute(
        select(MenuItem).where(MenuItem.id.in_(payload.item_ids))
    )
    found_items = result.scalars().all()

    found_ids = {item.id for item in found_items}
    available_items = [i for i in found_items if i.is_available]
    available_ids = {i.id for i in available_items}

    unavailable_ids = [
        iid for iid in payload.item_ids
        if iid not in found_ids or iid not in available_ids
    ]

    return BulkItemsResponse(
        items=[MenuItemResponse.model_validate(i) for i in available_items],
        unavailable_ids=unavailable_ids,
    )


@router.post("", response_model=MenuItemResponse, status_code=status.HTTP_201_CREATED, summary="Create Menu Item")
async def create_menu_item(
    payload: MenuItemCreate,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Protected. Verifies that the restaurant belongs to the requesting user."""
    res_result = await db.execute(select(Restaurant).where(Restaurant.id == payload.restaurant_id))
    restaurant = res_result.scalar_one_or_none()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    if restaurant.owner_user_id != user.get("user_id") and user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to add items to this restaurant")

    item = MenuItem(**payload.model_dump())
    db.add(item)
    await db.flush()
    await db.refresh(item)
    return item


@router.put("/{item_id}", response_model=MenuItemResponse, summary="Update Menu Item")
async def update_menu_item(
    item_id: str,
    payload: MenuItemUpdate,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Protected."""
    result = await db.execute(select(MenuItem).where(MenuItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Menu item not found")

    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(item, field, value)

    await db.flush()
    await db.refresh(item)
    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete Menu Item")
async def delete_menu_item(
    item_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    result = await db.execute(select(MenuItem).where(MenuItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Menu item not found")
    await db.delete(item)
    await db.flush()
