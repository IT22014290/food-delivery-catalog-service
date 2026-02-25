# 🍔 Food Delivery — Catalog Service

**SE4010 Cloud Computing Assignment | SLIIT 2026**

Microservice responsible for managing restaurants and menu items in the food delivery platform.

---

## Architecture Overview

```
                        ┌──────────────────────────────────────────────────┐
                        │              Food Delivery Platform               │
                        │                                                  │
   User ──► API GW ──►  │  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │
                        │  │  Auth    │  │ Catalog  │  │    Order     │  │
                        │  │ Service  │◄─┤ Service  │◄─┤   Service    │  │
                        │  │ :8001    │  │  :8000   │  │    :8002     │  │
                        │  └──────────┘  └──────────┘  └──────┬───────┘  │
                        │                                      │          │
                        │                              ┌───────▼───────┐  │
                        │                              │   Payment/    │  │
                        │                              │  Notification │  │
                        │                              │    :8003      │  │
                        │                              └───────────────┘  │
                        └──────────────────────────────────────────────────┘
```

### Inter-service Communication
| From | To | Endpoint | Purpose |
|------|-----|----------|---------|
| Catalog Service | Auth Service | `POST /api/v1/auth/verify` | Verify user JWT on protected routes |
| Order Service | Catalog Service | `POST /api/v1/menu-items/bulk-lookup` | Validate items & get prices for new orders |

---

## Tech Stack

| Component | Choice |
|-----------|--------|
| Language | Python 3.12 |
| Framework | FastAPI |
| ORM | SQLAlchemy (async) |
| Dev Database | SQLite (aiosqlite) |
| Prod Database | PostgreSQL (asyncpg) |
| Container | Docker (multi-stage) |
| Cloud | AWS ECS (Fargate) |
| Registry | Amazon ECR |
| CI/CD | GitHub Actions |
| SAST | SonarCloud + Snyk |

---

## Local Development

### Prerequisites
- Python 3.12+
- Docker Desktop

### Run locally
```bash
# Clone and setup
git clone https://github.com/YOUR_USERNAME/catalog-service.git
cd catalog-service

python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run the service
uvicorn src.main:app --reload --port 8000

# API docs available at:
# http://localhost:8000/docs        (Swagger UI)
# http://localhost:8000/redoc       (ReDoc)
# http://localhost:8000/openapi.json
```

### Run with Docker
```bash
docker build -t catalog-service .
docker run -p 8000:8000 \
  -e AUTH_REQUIRED=false \
  -e ENVIRONMENT=development \
  catalog-service
```

### Run tests
```bash
pip install pytest pytest-asyncio httpx pytest-cov
pytest tests/ -v --cov=src
```

---

## API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/health` | No | Health check |
| GET | `/api/v1/restaurants` | No | List restaurants |
| GET | `/api/v1/restaurants/{id}` | No | Get restaurant + menu |
| POST | `/api/v1/restaurants` | ✅ JWT | Create restaurant |
| PUT | `/api/v1/restaurants/{id}` | ✅ JWT | Update restaurant |
| DELETE | `/api/v1/restaurants/{id}` | ✅ JWT | Delete restaurant |
| GET | `/api/v1/menu-items` | No | List menu items |
| GET | `/api/v1/menu-items/{id}` | No | Get menu item |
| POST | `/api/v1/menu-items` | ✅ JWT | Create menu item |
| PUT | `/api/v1/menu-items/{id}` | ✅ JWT | Update menu item |
| DELETE | `/api/v1/menu-items/{id}` | ✅ JWT | Delete menu item |
| POST | `/api/v1/menu-items/bulk-lookup` | No | **Order Service integration** |

---

## AWS Deployment Guide (Free Tier)

### Step 1: Create ECR Repository
```bash
aws ecr create-repository \
  --repository-name food-delivery-catalog-service \
  --region us-east-1
```

### Step 2: Push Docker image
```bash
# Login to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

# Build and push
docker build -t food-delivery-catalog-service .
docker tag food-delivery-catalog-service:latest \
  YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/food-delivery-catalog-service:latest
docker push YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/food-delivery-catalog-service:latest
```

### Step 3: Create ECS Fargate Service
1. Go to AWS Console → ECS → Create Cluster (Fargate, free tier)
2. Create Task Definition → Fargate → 0.25 vCPU / 0.5 GB RAM (free tier eligible)
3. Set container image to your ECR URI
4. Set environment variables (AUTH_SERVICE_URL, DATABASE_URL)
5. Create Service → attach to your cluster
6. Add Application Load Balancer for public access

### Step 4: Set GitHub Secrets
```
AWS_ACCESS_KEY_ID     → Your IAM user access key
AWS_SECRET_ACCESS_KEY → Your IAM user secret key
SONAR_TOKEN           → From sonarcloud.io
SNYK_TOKEN            → From snyk.io
```

---

## Security Measures

| Measure | Implementation |
|---------|---------------|
| Authentication | JWT verification via Auth Service call |
| Authorization | Owner-based access control on write operations |
| Least Privilege | IAM role with only ECR pull + ECS exec permissions |
| Security Headers | X-Content-Type-Options, X-Frame-Options, HSTS, etc. |
| Non-root Container | Docker USER appuser |
| SAST | SonarCloud (in CI pipeline) |
| Dependency Scanning | Snyk (in CI pipeline) |
| Image Scanning | AWS ECR image vulnerability scanning |
| Input Validation | Pydantic v2 with field constraints |

---

## Project Structure

```
catalog-service/
├── src/
│   ├── main.py          # FastAPI app entry point
│   ├── database.py      # Async DB engine + session
│   ├── models.py        # SQLAlchemy ORM models
│   ├── schemas.py       # Pydantic request/response schemas
│   ├── middleware.py    # Security headers + JWT verification
│   └── routers/
│       ├── health.py    # /health endpoint
│       ├── restaurants.py
│       └── menu_items.py  # includes /bulk-lookup for Order Service
├── tests/
│   └── test_catalog.py
├── .github/
│   └── workflows/
│       └── ci-cd.yml    # GitHub Actions pipeline
├── Dockerfile           # Multi-stage, non-root
├── docker-compose.yml   # Local dev
├── openapi.yaml         # API contract
├── requirements.txt
└── sonar-project.properties
```
