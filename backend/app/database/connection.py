"""MongoDB connection singleton with retry logic.

Provides a single shared MongoClient instance with connection pooling.
Uses retry_with_backoff for the initial connection attempt to handle
transient network failures during startup.
"""

import logging
from typing import Optional

from pymongo import MongoClient
from pymongo.database import Database

from app.config.settings import Settings
from app.utils.retry import retry_with_backoff

logger = logging.getLogger(__name__)

_client: Optional[MongoClient] = None
_database: Optional[Database] = None


def get_database() -> Database:
    """Return a MongoDB database instance, creating the connection if needed.

    Uses a singleton pattern to reuse the same MongoClient across all
    callers. The initial connection is attempted with retry_with_backoff
    (3 retries, 1s initial backoff) to handle transient failures.

    Returns:
        A pymongo Database instance connected to the configured database.

    Raises:
        Exception: If the connection cannot be established after all retries.
    """
    global _client, _database

    if _database is not None:
        return _database

    settings = Settings.load()

    def _connect() -> MongoClient:
        logger.info("Connecting to MongoDB at %s...", settings.database_name)
        client = MongoClient(settings.mongodb_uri)
        # Force a connection attempt to verify connectivity
        client.admin.command("ping")
        logger.info("MongoDB connection established successfully.")
        return client

    _client = retry_with_backoff(fn=_connect, max_retries=3, initial_backoff=1.0)
    _database = _client[settings.database_name]

    return _database


def close_connection() -> None:
    """Close the MongoDB connection and reset the singleton state.

    Safe to call even if no connection has been established.
    """
    global _client, _database

    if _client is not None:
        _client.close()
        logger.info("MongoDB connection closed.")
        _client = None
        _database = None
