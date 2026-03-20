"""
Food Delivery App - Product/Item Catalog Service
SE4010 Cloud Computing Assignment 2026
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from pathlib import Path
import os
import logging

from .database import engine, Base
from .routers import restaurants, menu_items, health
from .middleware import SecurityHeadersMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# OpenAPI tag metadata — drives the Swagger UI section headers & descriptions
# ---------------------------------------------------------------------------
TAGS_METADATA = [
    {
        "name": "Health",
        "description": "Service liveness and readiness probes. Used by load-balancers and container orchestrators.",
    },
    {
        "name": "Restaurants",
        "description": (
            "Full CRUD for restaurant profiles. "
            "**Public** read endpoints are open; write operations require a valid JWT issued by the Auth Service."
        ),
    },
    {
        "name": "Menu Items",
        "description": (
            "Manage menu items belonging to a restaurant. "
            "Includes the **`/bulk-lookup`** endpoint consumed by the Order Service for inter-service order validation."
        ),
    },
]

DESCRIPTION = """
## Food Delivery — Catalog Service

Central registry for **restaurants** and their **menu items** in the food-delivery platform.

### Key capabilities
| Feature | Detail |
|---|---|
| Restaurant management | Create, read, update & soft-delete restaurant profiles |
| Menu management | Full CRUD for menu items with dietary and category filters |
| Bulk-lookup | Inter-service endpoint for the Order Service to validate items at checkout |
| Pagination | All list endpoints support `page` / `size` query parameters |
| Auth integration | Write operations validated against the Auth Service via JWT |

### Authentication
Protected endpoints require a **Bearer token** in the `Authorization` header:
```
Authorization: Bearer <jwt_token>
```
Tokens are issued by the **Auth Service** (`/auth/login`).

### Inter-service communication
The Order Service calls `POST /api/v1/menu-items/bulk-lookup` to validate item availability
and retrieve prices before creating an order.
"""


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Catalog Service started. DB tables ready.")
    yield
    await engine.dispose()
    logger.info("Catalog Service shutting down.")


app = FastAPI(
    title="Food Delivery — Catalog Service",
    description=DESCRIPTION,
    version="1.0.0",
    contact={
        "name": "SE4010 Cloud Computing — SLIIT",
        "url": "https://github.com",
    },
    license_info={
        "name": "MIT",
    },
    openapi_tags=TAGS_METADATA,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    swagger_ui_parameters={
        "deepLinking": True,
        "displayRequestDuration": True,
        "docExpansion": "list",
        "operationsSorter": "alpha",
        "filter": True,
        "syntaxHighlight.theme": "monokai",
        "tryItOutEnabled": True,
    },
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

# --- Frontend (must be mounted AFTER all API routes) ---
_static_dir = Path(__file__).parent / "static"
app.mount("/ui", StaticFiles(directory=str(_static_dir), html=True), name="frontend")
