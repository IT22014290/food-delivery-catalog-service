"""ORM Models for Catalog Service"""

from datetime import datetime
from sqlalchemy import Column, String, Float, Boolean, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship
from .database import Base
import uuid


def gen_uuid():
    return str(uuid.uuid4())


class Restaurant(Base):
    __tablename__ = "restaurants"

    id = Column(String, primary_key=True, default=gen_uuid)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    address = Column(String(500), nullable=False)
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    cuisine_type = Column(String(100), nullable=True)
    rating = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    image_url = Column(String(500), nullable=True)
    delivery_time_minutes = Column(Integer, default=30)
    minimum_order = Column(Float, default=0.0)
    owner_user_id = Column(String, nullable=True)  # From Auth Service
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    menu_items = relationship("MenuItem", back_populates="restaurant", cascade="all, delete-orphan")


class MenuItem(Base):
    __tablename__ = "menu_items"

    id = Column(String, primary_key=True, default=gen_uuid)
    restaurant_id = Column(String, ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)
    category = Column(String(100), nullable=True)
    image_url = Column(String(500), nullable=True)
    is_available = Column(Boolean, default=True)
    is_vegetarian = Column(Boolean, default=False)
    calories = Column(Integer, nullable=True)
    preparation_time_minutes = Column(Integer, default=15)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    restaurant = relationship("Restaurant", back_populates="menu_items")
