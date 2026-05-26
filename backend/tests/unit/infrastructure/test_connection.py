from unittest.mock import MagicMock, patch

import pytest


def test_get_session_yields_and_closes_session():
    """Verify that get_session yields and closes a database session."""
    with patch("infrastructure.db.connection.get_engine") as mock_get_engine, \
         patch("infrastructure.db.connection.Session") as mock_session_class:
        mock_engine = MagicMock()
        mock_get_engine.return_value = mock_engine

        mock_session_instance = MagicMock()
        mock_session_class.return_value.__enter__.return_value = mock_session_instance

        from infrastructure.db.connection import get_session

        session_gen = get_session()
        session = next(session_gen)

        # Assert session yielded is the one created by Session context manager
        assert session == mock_session_instance

        # Terminating generator should exit context manager
        with pytest.raises(StopIteration):
            next(session_gen)

        # Ensure enter and exit were triggered
        mock_session_class.return_value.__enter__.assert_called_once()
        mock_session_class.return_value.__exit__.assert_called_once()


def test_get_engine_raises_without_database_url():
    """Verify that get_engine raises if DATABASE_URL is not set."""
    with patch.dict("os.environ", {}, clear=True):
        # Reset the cached engine
        import infrastructure.db.connection as conn
        conn._engine = None

        with pytest.raises(ValueError, match="DATABASE_URL"):
            conn.get_engine()
