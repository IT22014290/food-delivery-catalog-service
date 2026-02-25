"""Health check endpoints"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from ..database import get_db
import os

router = APIRouter()


@router.get("/health", summary="Health Check")
async def health_check(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception:
        db_status = "unhealthy"

    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "service": "catalog-service",
        "version": "1.0.0",
        "database": db_status,
        "environment": os.getenv("ENVIRONMENT", "development"),
    }


@router.get("/", summary="Root")
async def root():
    return {
        "service": "Food Delivery - Catalog Service",
        "version": "1.0.0",
        "docs": "/docs",
    }
