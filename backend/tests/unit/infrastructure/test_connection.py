from unittest.mock import MagicMock, patch

import pytest
from infrastructure.db.connection import get_session


def test_get_session_yields_and_closes_session():
    """Verify that get_session yields and closes a database session."""
    with patch("infrastructure.db.connection.Session") as mock_session_class:
        mock_session_instance = MagicMock()
        # Mock the context manager behavior of Session
        mock_session_class.return_value.__enter__.return_value = mock_session_instance

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
