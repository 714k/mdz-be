## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     mdz BACKEND                       │
│                                                             │
│  ┌────────────────┐      ┌──────────────┐                 │
│  │   FastAPI      │─────▶│  PostgreSQL  │                 │
│  │   REST API     │      │   (Primary)  │                 │
│  └────────┬───────┘      └──────────────┘                 │
│           │                                                 │
│           │              ┌──────────────┐                 │
│           └─────────────▶│    Redis     │                 │
│                          │ (Cache/Auth) │                 │
│  ┌────────────────┐      └──────────────┘                 │
│  │  Prometheus    │                                        │
│  │  /metrics      │      ┌──────────────┐                 │
│  └────────────────┘      │   Logging    │                 │
│                          │ (Structured) │                 │
│                          └──────────────┘                 │
└─────────────────────────────────────────────────────────────┘
          │
          │ HTTP/WebSocket
          ▼
   ┌──────────────┐
   │  VS Code     │
   │  Extension   │
   └──────────────┘
```

---

## Folder Structure

```
mdz/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI application entry
│   │   ├── config.py               # Environment configuration
│   │   ├── dependencies.py         # Dependency injection
│   │   │
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── v1/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── router.py       # API version router
│   │   │   │   ├── auth.py         # Authentication endpoints
│   │   │   │   ├── health.py       # Health checks
│   │   │   │   └── chat.py         # Chat endpoints (stub)
│   │   │
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── security.py         # JWT, hashing, CSP
│   │   │   ├── database.py         # DB session management
│   │   │   ├── cache.py            # Redis client
│   │   │   ├── logging.py          # Structured logging
│   │   │   └── monitoring.py       # Prometheus metrics
│   │   │
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── user.py             # User SQLAlchemy model
│   │   │   └── session.py          # Session model
│   │   │
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py             # Pydantic auth schemas
│   │   │   └── health.py           # Health check schemas
│   │   │
│   │   └── middleware/
│   │       ├── __init__.py
│   │       ├── cors.py             # CORS configuration
│   │       ├── rate_limit.py       # Redis-based rate limiting
│   │       └── error_handler.py    # Global exception handling
│   │
│   ├── alembic/                    # Database migrations
│   │   ├── versions/
│   │   └── env.py
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_auth.py
│   │   └── test_health.py
│   │
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   ├── .env.example
│   ├── alembic.ini
│   ├── pytest.ini
│   └── mypy.ini
│
├── docker/
│   ├── Dockerfile.backend
│   ├── docker-compose.yml
│   └── postgres/
│       └── init.sql
│
├── scripts/
│   ├── init_db.sh
│   ├── run_dev.sh
│   └── run_tests.sh
│
└── README.md
```