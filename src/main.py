"""
Food Delivery App - Product/Item Catalog Service
SE4010 Cloud Computing Assignment 2026
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from contextlib import asynccontextmanager
import httpx
import os
import logging

from .database import engine, Base
from .routers import restaurants, menu_items, health
from .middleware import SecurityHeadersMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create DB tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Catalog Service started. DB tables ready.")
    yield
    # Shutdown
    await engine.dispose()
    logger.info("Catalog Service shutting down.")


app = FastAPI(
    title="Food Delivery - Catalog Service",
    description="Manages restaurants and menu items for the food delivery platform.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# --- Middleware ---
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# --- Routers ---
app.include_router(health.router, tags=["Health"])
app.include_router(restaurants.router, prefix="/api/v1/restaurants", tags=["Restaurants"])
app.include_router(menu_items.router, prefix="/api/v1/menu-items", tags=["Menu Items"])
