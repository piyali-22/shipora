"""
MongoDB connection handling via Motor (async driver).

One client is created at app startup and reused everywhere via
get_db(). Collections are exposed as named accessors so the rest of
the codebase never hardcodes collection name strings.
"""
import logging

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from core.config import get_settings

logger = logging.getLogger("shipora.database")

_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None


async def connect_to_mongo() -> None:
    """Called once on app startup."""
    global _client, _db
    settings = get_settings()
    _client = AsyncIOMotorClient(settings.mongo_uri, serverSelectionTimeoutMS=5000)
    _db = _client[settings.mongo_db_name]

    # Fail loudly at startup rather than silently later, but don't crash
    # local dev if Mongo just isn't up yet — log clearly instead.
    try:
        await _client.admin.command("ping")
        logger.info("Connected to MongoDB database '%s'", settings.mongo_db_name)
        await ensure_indexes(_db)
    except Exception as exc:  # noqa: BLE001
        logger.error(
            "Could not reach MongoDB at startup (%s). "
            "The app will keep running, but requests touching the DB will fail "
            "until MONGO_URI is reachable.",
            exc,
        )


async def close_mongo_connection() -> None:
    global _client
    if _client is not None:
        _client.close()
        logger.info("MongoDB connection closed")


def get_db() -> AsyncIOMotorDatabase:
    if _db is None:
        raise RuntimeError(
            "Database not initialized yet. connect_to_mongo() must run at app startup."
        )
    return _db


async def ensure_indexes(db: AsyncIOMotorDatabase) -> None:
    """
    Create indexes required for correctness and query performance.
    Safe to call repeatedly — create_index is idempotent per index spec.
    """
    await db.users.create_index("email", unique=True)

    await db.orders.create_index("tracking_id", unique=True)
    await db.orders.create_index("customer_id")
    await db.orders.create_index("assigned_agent_id")
    await db.orders.create_index("current_status")
    await db.orders.create_index("created_at")

    await db.agents.create_index("user_id", unique=True)
    await db.agents.create_index("current_zone_id")
    await db.agents.create_index("is_available")

    await db.zones.create_index("pincodes")
    await db.zones.create_index("is_active")

    await db.rate_cards.create_index([("order_type", 1), ("scope", 1), ("is_active", 1)])

    await db.tracking_events.create_index("order_id")
    await db.tracking_events.create_index([("order_id", 1), ("timestamp", 1)])

    await db.delivery_attempts.create_index("order_id")

    await db.notifications.create_index("recipient_id")
    await db.notifications.create_index("created_at")

    await db.audit_logs.create_index("order_id")

    logger.info("Indexes ensured")
