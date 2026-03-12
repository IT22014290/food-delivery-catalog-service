"""Health check endpoints"""

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from ..database import get_db
import os

router = APIRouter()

_LANDING_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Catalog Service — Food Delivery Platform</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background: #0f1117;
      color: #e2e8f0;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 3rem 1rem 4rem;
    }
    /* ---- Hero ---- */
    .hero {
      text-align: center;
      max-width: 680px;
      margin-bottom: 3rem;
    }
    .badge {
      display: inline-block;
      background: linear-gradient(135deg, #f97316, #ef4444);
      color: #fff;
      font-size: 0.72rem;
      font-weight: 700;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      padding: 0.3rem 0.85rem;
      border-radius: 99px;
      margin-bottom: 1.25rem;
    }
    h1 {
      font-size: clamp(1.8rem, 5vw, 2.8rem);
      font-weight: 800;
      line-height: 1.15;
      background: linear-gradient(135deg, #f97316 0%, #fb923c 40%, #fbbf24 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
      margin-bottom: 1rem;
    }
    .subtitle {
      color: #94a3b8;
      font-size: 1.05rem;
      line-height: 1.7;
    }
    /* ---- Cards grid ---- */
    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 1.25rem;
      width: 100%;
      max-width: 860px;
      margin-bottom: 3rem;
    }
    .card {
      background: #1e2230;
      border: 1px solid #2d3448;
      border-radius: 14px;
      padding: 1.5rem 1.4rem;
      transition: border-color 0.2s, transform 0.15s;
    }
    .card:hover { border-color: #f97316; transform: translateY(-3px); }
    .card-icon { font-size: 1.6rem; margin-bottom: 0.65rem; }
    .card h3 { font-size: 0.95rem; font-weight: 700; margin-bottom: 0.4rem; color: #f1f5f9; }
    .card p  { font-size: 0.82rem; color: #64748b; line-height: 1.55; }
    /* ---- Quick links ---- */
    .links {
      display: flex;
      flex-wrap: wrap;
      gap: 0.9rem;
      justify-content: center;
      margin-bottom: 3rem;
    }
    .btn {
      display: inline-flex;
      align-items: center;
      gap: 0.45rem;
      padding: 0.65rem 1.4rem;
      border-radius: 10px;
      font-size: 0.9rem;
      font-weight: 600;
      text-decoration: none;
      transition: opacity 0.15s, transform 0.15s;
    }
    .btn:hover { opacity: 0.85; transform: translateY(-1px); }
    .btn-primary   { background: linear-gradient(135deg, #f97316, #ef4444); color: #fff; }
    .btn-secondary { background: #1e2230; border: 1px solid #2d3448; color: #cbd5e1; }
    /* ---- Endpoints table ---- */
    .section-title {
      font-size: 0.75rem;
      font-weight: 700;
      letter-spacing: 0.1em;
      text-transform: uppercase;
      color: #475569;
      margin-bottom: 1rem;
      text-align: center;
    }
    table {
      width: 100%;
      max-width: 860px;
      border-collapse: collapse;
      font-size: 0.83rem;
    }
    th {
      text-align: left;
      padding: 0.55rem 0.9rem;
      background: #161a27;
      color: #64748b;
      font-weight: 600;
      border-bottom: 1px solid #2d3448;
    }
    td {
      padding: 0.6rem 0.9rem;
      border-bottom: 1px solid #1e2230;
      color: #94a3b8;
    }
    tr:hover td { background: #1a1f30; }
    .method {
      display: inline-block;
      font-size: 0.7rem;
      font-weight: 700;
      padding: 0.2rem 0.55rem;
      border-radius: 5px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .get    { background: #0e4429; color: #3fb950; }
    .post   { background: #1c3a6e; color: #79b8ff; }
    .put    { background: #3d2a00; color: #e3b341; }
    .delete { background: #3d0a14; color: #ff7b72; }
    .path   { font-family: "SFMono-Regular", Consolas, monospace; color: #e2e8f0; }
    .lock   { color: #f97316; font-size: 0.8rem; }
    /* ---- Footer ---- */
    footer { margin-top: 2.5rem; font-size: 0.78rem; color: #334155; text-align: center; }
  </style>
</head>
<body>

  <div class="hero">
    <span class="badge">Microservice &bull; v1.0.0</span>
    <h1>Food Delivery<br>Catalog Service</h1>
    <p class="subtitle">
      Central registry for restaurants and menu items.<br>
      Provides REST APIs consumed by the web client, mobile app, and Order Service.
    </p>
  </div>

  <div class="links">
    <a class="btn btn-primary"    href="/ui/">&#9776; Dashboard</a>
    <a class="btn btn-secondary"  href="/docs">&#9654; Swagger UI</a>
    <a class="btn btn-secondary"  href="/redoc">&#9636; ReDoc</a>
    <a class="btn btn-secondary"  href="/openapi.json">&#9741; OpenAPI JSON</a>
    <a class="btn btn-secondary"  href="/health">&#9679; Health</a>
  </div>

  <div class="grid">
    <div class="card">
      <div class="card-icon">&#127830;</div>
      <h3>Restaurants</h3>
      <p>List, create, update and soft-delete restaurant profiles with cuisine filters and pagination.</p>
    </div>
    <div class="card">
      <div class="card-icon">&#128203;</div>
      <h3>Menu Items</h3>
      <p>Full CRUD for menu items. Filter by category, dietary type, or restaurant.</p>
    </div>
    <div class="card">
      <div class="card-icon">&#128279;</div>
      <h3>Bulk Lookup</h3>
      <p>Inter-service endpoint called by the Order Service to validate items and fetch prices at checkout.</p>
    </div>
    <div class="card">
      <div class="card-icon">&#128274;</div>
      <h3>JWT Auth</h3>
      <p>Write operations validated against the Auth Service. Read endpoints are open to all consumers.</p>
    </div>
  </div>

  <p class="section-title">API Endpoints</p>
  <table>
    <thead>
      <tr>
        <th>Method</th>
        <th>Path</th>
        <th>Description</th>
        <th>Auth</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><span class="method get">GET</span></td>
        <td class="path">/api/v1/restaurants</td>
        <td>List restaurants (paginated, filterable)</td>
        <td></td>
      </tr>
      <tr>
        <td><span class="method get">GET</span></td>
        <td class="path">/api/v1/restaurants/{id}</td>
        <td>Get restaurant with full menu</td>
        <td></td>
      </tr>
      <tr>
        <td><span class="method post">POST</span></td>
        <td class="path">/api/v1/restaurants</td>
        <td>Create a new restaurant</td>
        <td><span class="lock">&#128274;</span></td>
      </tr>
      <tr>
        <td><span class="method put">PUT</span></td>
        <td class="path">/api/v1/restaurants/{id}</td>
        <td>Update restaurant details</td>
        <td><span class="lock">&#128274;</span></td>
      </tr>
      <tr>
        <td><span class="method delete">DELETE</span></td>
        <td class="path">/api/v1/restaurants/{id}</td>
        <td>Soft-delete a restaurant</td>
        <td><span class="lock">&#128274;</span></td>
      </tr>
      <tr>
        <td><span class="method get">GET</span></td>
        <td class="path">/api/v1/menu-items</td>
        <td>List menu items (filterable)</td>
        <td></td>
      </tr>
      <tr>
        <td><span class="method get">GET</span></td>
        <td class="path">/api/v1/menu-items/{id}</td>
        <td>Get a single menu item</td>
        <td></td>
      </tr>
      <tr>
        <td><span class="method post">POST</span></td>
        <td class="path">/api/v1/menu-items/bulk-lookup</td>
        <td>Validate &amp; fetch items by IDs (Order Service)</td>
        <td></td>
      </tr>
      <tr>
        <td><span class="method post">POST</span></td>
        <td class="path">/api/v1/menu-items</td>
        <td>Add a menu item to a restaurant</td>
        <td><span class="lock">&#128274;</span></td>
      </tr>
      <tr>
        <td><span class="method put">PUT</span></td>
        <td class="path">/api/v1/menu-items/{id}</td>
        <td>Update a menu item</td>
        <td><span class="lock">&#128274;</span></td>
      </tr>
      <tr>
        <td><span class="method delete">DELETE</span></td>
        <td class="path">/api/v1/menu-items/{id}</td>
        <td>Remove a menu item</td>
        <td><span class="lock">&#128274;</span></td>
      </tr>
      <tr>
        <td><span class="method get">GET</span></td>
        <td class="path">/health</td>
        <td>Liveness &amp; database health check</td>
        <td></td>
      </tr>
    </tbody>
  </table>

  <footer>
    SE4010 Cloud Computing &bull; SLIIT &bull; 2026 &bull;
    Built with FastAPI &bull; Deployed on AWS ECS Fargate
  </footer>

</body>
</html>"""


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


@router.get("/", summary="Landing Page", response_class=HTMLResponse, include_in_schema=False)
async def root():
    return HTMLResponse(content=_LANDING_HTML)
