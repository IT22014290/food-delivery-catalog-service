"""Restaurants CRUD endpoints"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
import math

from ..database import get_db
from ..models import Restaurant
from ..schemas import (
    RestaurantCreate, RestaurantUpdate,
    RestaurantResponse, RestaurantWithMenuResponse, PaginatedResponse
)
from ..middleware import security, get_current_user, get_optional_user

router = APIRouter()


@router.get("", response_model=PaginatedResponse, summary="List Restaurants")
async def list_restaurants(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    cuisine_type: Optional[str] = None,
    is_active: bool = True,
    db: AsyncSession = Depends(get_db),
    _user=Depends(get_optional_user),
):
    """Public endpoint. Returns paginated list of restaurants."""
    query = select(Restaurant).where(Restaurant.is_active == is_active)
    if cuisine_type:
        query = query.where(Restaurant.cuisine_type.ilike(f"%{cuisine_type}%"))

    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar()

    query = query.offset((page - 1) * size).limit(size)
    result = await db.execute(query)
    restaurants = result.scalars().all()

    return PaginatedResponse(
        items=[RestaurantResponse.model_validate(r) for r in restaurants],
        total=total,
        page=page,
        size=size,
        pages=math.ceil(total / size) if total else 0,
    )


@router.get("/{restaurant_id}", response_model=RestaurantWithMenuResponse, summary="Get Restaurant with Menu")
async def get_restaurant(
    restaurant_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Public endpoint. Returns restaurant details including full menu."""
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(Restaurant)
        .options(selectinload(Restaurant.menu_items))
        .where(Restaurant.id == restaurant_id)
    )
    restaurant = result.scalar_one_or_none()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return restaurant


@router.post("", response_model=RestaurantResponse, status_code=status.HTTP_201_CREATED, summary="Create Restaurant")
async def create_restaurant(
    payload: RestaurantCreate,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
    credentials=Depends(security),
):
    """Protected. Requires valid JWT from Auth Service."""
    restaurant = Restaurant(**payload.model_dump(), owner_user_id=user.get("user_id"))
    db.add(restaurant)
    await db.flush()
    await db.refresh(restaurant)
    return restaurant


@router.put("/{restaurant_id}", response_model=RestaurantResponse, summary="Update Restaurant")
async def update_restaurant(
    restaurant_id: str,
    payload: RestaurantUpdate,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
    credentials=Depends(security),
):
    """Protected. Only the owner or admin can update."""
    result = await db.execute(select(Restaurant).where(Restaurant.id == restaurant_id))
    restaurant = result.scalar_one_or_none()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    if restaurant.owner_user_id != user.get("user_id") and user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to update this restaurant")

    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(restaurant, field, value)

    await db.flush()
    await db.refresh(restaurant)
    return restaurant


@router.delete("/{restaurant_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete Restaurant")
async def delete_restaurant(
    restaurant_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
    credentials=Depends(security),
):
    """Protected. Soft-deletes by setting is_active=False."""
    result = await db.execute(select(Restaurant).where(Restaurant.id == restaurant_id))
    restaurant = result.scalar_one_or_none()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    if restaurant.owner_user_id != user.get("user_id") and user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    restaurant.is_active = False
    await db.flush()
