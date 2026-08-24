"""
SHIPORA — Smart Last-Mile Logistics Platform
Backend entrypoint.

This file wires together the app instance, CORS, DB lifecycle, and
route routers. Business logic never lives here — only app setup.
Route modules are mounted as they're built out in later phases.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import get_settings
from core.database import connect_to_mongo, close_mongo_connection, get_db

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("shipora")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()
    yield
    await close_mongo_connection()


settings = get_settings()

app = FastAPI(
    title="Shipora API",
    description="Smart Last-Mile Logistics Platform — backend API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health_check():
    """
    Basic liveness + DB reachability check.
    Does not require auth — used for deploy/monitoring checks.
    """
    db_status = "unknown"
    try:
        db = get_db()
        await db.command("ping")
        db_status = "connected"
    except Exception as exc:  # noqa: BLE001
        db_status = f"unreachable ({exc.__class__.__name__})"

    return {
        "service": "shipora-api",
        "status": "ok",
        "environment": settings.app_env,
        "database": db_status,
    }


# --- Routers ---
from routes import auth, zones, rate_card, orders, agents, notifications  # noqa: E402

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(zones.router, prefix="/api/zones", tags=["zones"])
app.include_router(rate_card.router, prefix="/api/rates", tags=["rate cards"])
app.include_router(orders.router, prefix="/api/orders", tags=["orders"])
app.include_router(agents.router, prefix="/api/agents", tags=["agents"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["notifications"])
