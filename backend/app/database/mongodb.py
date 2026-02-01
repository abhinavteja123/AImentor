"""
MongoDB Connection using Motor (async driver)
"""

import logging
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from ..config import settings

logger = logging.getLogger(__name__)

# MongoDB client instance
_client: AsyncIOMotorClient = None
_database: AsyncIOMotorDatabase = None
_connection_failed: bool = False


async def init_mongodb():
    """Initialize MongoDB connection with proper SSL config for serverless."""
    global _client, _database, _connection_failed
    
    try:
        # Configure Motor client - SSL settings only for MongoDB Atlas
        # For local MongoDB, don't use SSL
        connection_params = {
            "serverSelectionTimeoutMS": 5000,
            "connectTimeoutMS": 5000,
            "socketTimeoutMS": 5000,
            "retryWrites": True,
        }
        
        # Only add SSL settings if connecting to MongoDB Atlas (remote)
        if "mongodb+srv" in settings.MONGODB_URL or "ssl=true" in settings.MONGODB_URL.lower():
            connection_params["tlsAllowInvalidCertificates"] = False
            connection_params["directConnection"] = False
        
        _client = AsyncIOMotorClient(settings.MONGODB_URL, **connection_params)
        _database = _client[settings.MONGODB_DB]
        
        # Test connection with shorter timeout
        await _client.admin.command("ping")
        logger.info("MongoDB connected successfully")
        _connection_failed = False
        
    except Exception as e:
        logger.warning(f"MongoDB connection failed (non-critical): {str(e)[:200]}")
        logger.info("Application will continue without MongoDB (chat features may be limited)")
        _connection_failed = True
        # Don't raise - allow app to start without MongoDB


async def close_mongodb():
    """Close MongoDB connection."""
    global _client
    if _client:
        _client.close()


def get_mongodb() -> AsyncIOMotorDatabase:
    """Get MongoDB database instance."""
    if _connection_failed or _database is None:
        logger.warning("MongoDB not available")
        return None
    return _database


def is_mongodb_available() -> bool:
    """Check if MongoDB is available."""
    return not _connection_failed and _database is not None


# Collections
def get_conversations_collection():
    """Get conversations collection for chat history."""
    if not is_mongodb_available():
        return None
    return _database["conversations"]


def get_chat_sessions_collection():
    """Get chat sessions collection."""
    if not is_mongodb_available():
        return None
    return _database["chat_sessions"]


def get_memory_collection():
    """Get memory collection for user memories."""
    if not is_mongodb_available():
        return None
    return _database["memories"]
