"""Pydantic schemas for request/response validation"""

from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List
from datetime import datetime


# ── Restaurant Schemas ──────────────────────────────────────────────────────

class RestaurantBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    address: str = Field(..., min_length=5)
    phone: Optional[str] = None
    email: Optional[str] = None
    cuisine_type: Optional[str] = None
    image_url: Optional[str] = None
    delivery_time_minutes: int = Field(default=30, ge=5, le=180)
    minimum_order: float = Field(default=0.0, ge=0)


class RestaurantCreate(RestaurantBase):
    owner_user_id: Optional[str] = None


class RestaurantUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    cuisine_type: Optional[str] = None
    image_url: Optional[str] = None
    delivery_time_minutes: Optional[int] = Field(None, ge=5, le=180)
    minimum_order: Optional[float] = Field(None, ge=0)
    is_active: Optional[bool] = None


class RestaurantResponse(RestaurantBase):
    id: str
    rating: float
    is_active: bool
    owner_user_id: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RestaurantWithMenuResponse(RestaurantResponse):
    menu_items: List["MenuItemResponse"] = []


# ── Menu Item Schemas ────────────────────────────────────────────────────────

class MenuItemBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    price: float = Field(..., gt=0)
    category: Optional[str] = None
    image_url: Optional[str] = None
    is_available: bool = True
    is_vegetarian: bool = False
    calories: Optional[int] = Field(None, ge=0)
    preparation_time_minutes: int = Field(default=15, ge=1, le=120)


class MenuItemCreate(MenuItemBase):
    restaurant_id: str


class MenuItemUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    category: Optional[str] = None
    image_url: Optional[str] = None
    is_available: Optional[bool] = None
    is_vegetarian: Optional[bool] = None
    calories: Optional[int] = Field(None, ge=0)
    preparation_time_minutes: Optional[int] = Field(None, ge=1, le=120)


class MenuItemResponse(MenuItemBase):
    id: str
    restaurant_id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Shared Response Schemas ──────────────────────────────────────────────────

class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    size: int
    pages: int


class BulkItemsRequest(BaseModel):
    """Used by Order Service to validate items before placing an order"""
    item_ids: List[str]


class BulkItemsResponse(BaseModel):
    """Response sent to Order Service"""
    items: List[MenuItemResponse]
    unavailable_ids: List[str]


RestaurantWithMenuResponse.model_rebuild()
