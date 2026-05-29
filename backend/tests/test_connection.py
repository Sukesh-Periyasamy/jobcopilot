"""Unit tests for the MongoDB connection singleton."""

import os
from unittest.mock import MagicMock, patch

import pytest

from app.database import connection
from app.database.connection import close_connection, get_database


@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset the module-level singleton state before and after each test."""
    connection._client = None
    connection._database = None
    yield
    connection._client = None
    connection._database = None


class TestGetDatabase:
    """Tests for get_database() singleton behavior."""

    @patch.dict(os.environ, {"MONGODB_URI": "mongodb://localhost:27017/testdb"}, clear=True)
    @patch("app.database.connection.MongoClient")
    def test_returns_database_instance(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client.__getitem__ = MagicMock(return_value=MagicMock())
        mock_client.admin.command.return_value = {"ok": 1}
        mock_client_cls.return_value = mock_client

        db = get_database()

        assert db is not None
        mock_client_cls.assert_called_once_with("mongodb://localhost:27017/testdb")
        mock_client.admin.command.assert_called_once_with("ping")

    @patch.dict(os.environ, {"MONGODB_URI": "mongodb://localhost:27017/testdb"}, clear=True)
    @patch("app.database.connection.MongoClient")
    def test_singleton_returns_same_instance(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client.admin.command.return_value = {"ok": 1}
        mock_client_cls.return_value = mock_client

        db1 = get_database()
        db2 = get_database()

        assert db1 is db2
        # MongoClient should only be instantiated once
        mock_client_cls.assert_called_once()

    @patch.dict(os.environ, {"MONGODB_URI": "mongodb://localhost:27017/testdb"}, clear=True)
    @patch("app.database.connection.MongoClient")
    def test_uses_configured_database_name(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client.admin.command.return_value = {"ok": 1}
        mock_client_cls.return_value = mock_client

        get_database()

        # Default database_name is "jobcopilot"
        mock_client.__getitem__.assert_called_with("jobcopilot")

    @patch.dict(
        os.environ,
        {"MONGODB_URI": "mongodb://localhost:27017/testdb", "DATABASE_NAME": "mydb"},
        clear=True,
    )
    @patch("app.database.connection.MongoClient")
    def test_uses_custom_database_name(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client.admin.command.return_value = {"ok": 1}
        mock_client_cls.return_value = mock_client

        get_database()

        mock_client.__getitem__.assert_called_with("mydb")

    @patch.dict(os.environ, {"MONGODB_URI": "mongodb://localhost:27017/testdb"}, clear=True)
    @patch("app.database.connection.retry_with_backoff")
    def test_uses_retry_with_backoff(self, mock_retry):
        mock_client = MagicMock()
        mock_client.admin.command.return_value = {"ok": 1}
        mock_retry.return_value = mock_client

        get_database()

        mock_retry.assert_called_once()
        call_kwargs = mock_retry.call_args
        assert call_kwargs.kwargs["max_retries"] == 3
        assert call_kwargs.kwargs["initial_backoff"] == 1.0

    @patch.dict(os.environ, {"MONGODB_URI": "mongodb://localhost:27017/testdb"}, clear=True)
    @patch("app.database.connection.retry_with_backoff")
    def test_raises_after_retries_exhausted(self, mock_retry):
        mock_retry.side_effect = ConnectionError("Cannot connect to MongoDB")

        with pytest.raises(ConnectionError, match="Cannot connect to MongoDB"):
            get_database()


class TestCloseConnection:
    """Tests for close_connection()."""

    @patch.dict(os.environ, {"MONGODB_URI": "mongodb://localhost:27017/testdb"}, clear=True)
    @patch("app.database.connection.MongoClient")
    def test_closes_client_and_resets_state(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client.admin.command.return_value = {"ok": 1}
        mock_client_cls.return_value = mock_client

        get_database()
        close_connection()

        mock_client.close.assert_called_once()
        assert connection._client is None
        assert connection._database is None

    def test_close_when_no_connection_is_safe(self):
        # Should not raise even if no connection was established
        close_connection()

    @patch.dict(os.environ, {"MONGODB_URI": "mongodb://localhost:27017/testdb"}, clear=True)
    @patch("app.database.connection.MongoClient")
    def test_new_connection_after_close(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client.admin.command.return_value = {"ok": 1}
        mock_client_cls.return_value = mock_client

        db1 = get_database()
        close_connection()
        db2 = get_database()

        # After close, a new connection should be created
        assert mock_client_cls.call_count == 2
