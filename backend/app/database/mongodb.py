"""
MongoDB Connection using Motor (async driver)
"""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.config import settings

# MongoDB client instance
_client: AsyncIOMotorClient = None
_database: AsyncIOMotorDatabase = None


async def init_mongodb():
    """Initialize MongoDB connection."""
    global _client, _database
    _client = AsyncIOMotorClient(settings.MONGODB_URL)
    _database = _client[settings.MONGODB_DB]
    
    # Test connection
    await _client.admin.command("ping")


async def close_mongodb():
    """Close MongoDB connection."""
    global _client
    if _client:
        _client.close()


def get_mongodb() -> AsyncIOMotorDatabase:
    """Get MongoDB database instance."""
    return _database


# Collections
def get_conversations_collection():
    """Get conversations collection for chat history."""
    return _database["conversations"]


def get_chat_sessions_collection():
    """Get chat sessions collection."""
    return _database["chat_sessions"]


def get_memory_collection():
    """Get memory collection for user memories."""
    return _database["memories"]
