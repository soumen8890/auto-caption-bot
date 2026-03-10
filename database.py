"""
database.py — MongoDB Atlas helper using motor (async).

Collections:
  users       — per-user settings & stats
  chats       — per-chat (group/channel) settings
  cache       — IMDB lookup cache (TTL index)
  stats       — global counters
"""

import logging
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from config import Config

logger = logging.getLogger(__name__)

_client: AsyncIOMotorClient | None = None
_db = None


# ──────────────────────────── Connection ────────────────────────────

async def connect_db():
    global _client, _db
    if _client:
        return
    try:
        _client = AsyncIOMotorClient(Config.MONGO_URI, serverSelectionTimeoutMS=5000)
        _db = _client[Config.DB_NAME]

        # TTL index on cache — auto-expire after 7 days
        await _db.cache.create_index("created_at", expireAfterSeconds=604800)

        # Unique indexes
        await _db.users.create_index("user_id", unique=True)
        await _db.chats.create_index("chat_id", unique=True)

        logger.info("✅ MongoDB connected: %s", Config.DB_NAME)
    except Exception as e:
        logger.error("❌ MongoDB connection failed: %s", e)
        raise


async def close_db():
    global _client
    if _client:
        _client.close()
        _client = None
        logger.info("MongoDB disconnected.")


def get_db():
    if _db is None:
        raise RuntimeError("DB not initialised — call connect_db() first.")
    return _db


# ──────────────────────────── Users ────────────────────────────

async def get_user(user_id: int) -> dict:
    db = get_db()
    doc = await db.users.find_one({"user_id": user_id})
    if not doc:
        doc = {
            "user_id": user_id,
            "template": Config.DEFAULT_TEMPLATE,
            "auto_caption": True,
            "files_processed": 0,
            "joined_at": datetime.now(timezone.utc),
        }
        await db.users.insert_one(doc)
    return doc


async def update_user(user_id: int, data: dict):
    db = get_db()
    await db.users.update_one(
        {"user_id": user_id},
        {"$set": data},
        upsert=True
    )


async def increment_user_stat(user_id: int, field: str = "files_processed"):
    db = get_db()
    await db.users.update_one(
        {"user_id": user_id},
        {"$inc": {field: 1}},
        upsert=True
    )


async def get_all_users() -> list[dict]:
    db = get_db()
    return await db.users.find({}, {"user_id": 1}).to_list(length=None)


# ──────────────────────────── Chats ────────────────────────────

async def get_chat(chat_id: int) -> dict:
    db = get_db()
    doc = await db.chats.find_one({"chat_id": chat_id})
    if not doc:
        doc = {
            "chat_id": chat_id,
            "template": Config.DEFAULT_TEMPLATE,
            "auto_caption": True,
            "added_at": datetime.now(timezone.utc),
        }
        await db.chats.insert_one(doc)
    return doc


async def update_chat(chat_id: int, data: dict):
    db = get_db()
    await db.chats.update_one(
        {"chat_id": chat_id},
        {"$set": data},
        upsert=True
    )


# ──────────────────────────── IMDB Cache ────────────────────────────

async def get_cached(imdb_id: str) -> dict | None:
    db = get_db()
    doc = await db.cache.find_one({"imdb_id": imdb_id})
    return doc.get("data") if doc else None


async def set_cache(imdb_id: str, data: dict):
    db = get_db()
    await db.cache.update_one(
        {"imdb_id": imdb_id},
        {"$set": {"imdb_id": imdb_id, "data": data, "created_at": datetime.now(timezone.utc)}},
        upsert=True
    )


# ──────────────────────────── Global Stats ────────────────────────────

async def increment_global(field: str):
    db = get_db()
    await db.stats.update_one(
        {"_id": "global"},
        {"$inc": {field: 1}},
        upsert=True
    )


async def get_global_stats() -> dict:
    db = get_db()
    doc = await db.stats.find_one({"_id": "global"})
    return doc or {}


async def get_total_users() -> int:
    db = get_db()
    return await db.users.count_documents({})


async def get_total_chats() -> int:
    db = get_db()
    return await db.chats.count_documents({})
