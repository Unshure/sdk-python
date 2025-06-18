"""Tests for Agent customer state management functionality."""

from unittest.mock import Mock, patch
import pytest

from strands.agent.agent import Agent
from strands.persistence.exceptions import PersistenceException
from strands.persistence.persistence_manager import PersistenceManager


class TestAgentCustomerState:
    """Test Agent customer state management methods."""

    @pytest.fixture
    def mock_persistence_manager(self):
        """Create a mock persistence manager for testing."""
        mock_manager = Mock(spec=PersistenceManager)
        mock_manager.session_exists.return_value = False
        mock_manager.load_agent_state.return_value = []
        mock_manager.load_customer_state.return_value = {}
        mock_manager.load_request_state.return_value = None
        return mock_manager

    @pytest.fixture
    def agent_without_persistence(self):
        """Create an agent without persistence for testing."""
        return Agent()

    @pytest.fixture
    def agent_with_persistence(self, mock_persistence_manager):
        """Create an agent with persistence for testing."""
        return Agent(persistence_manager=mock_persistence_manager, session_id="test_session", user_id="test_user")

    def test_initial_customer_state_empty(self, agent_without_persistence):
        """Test that customer state is initially empty."""
        assert agent_without_persistence.customer_state == {}
        assert agent_without_persistence.get_customer_state() == {}

    def test_update_customer_state_without_persistence(self, agent_without_persistence):
        """Test updating customer state without persistence."""
        updates = {"preference": "concise", "language": "en"}

        agent_without_persistence.update_customer_state(updates)

        assert agent_without_persistence.customer_state == updates
        assert agent_without_persistence.get_customer_state() == updates

    def test_update_customer_state_with_persistence(self, agent_with_persistence):
        """Test updating customer state with persistence."""
        updates = {"preference": "concise", "language": "en"}

        # Mock the persistence callback method
        with patch.object(agent_with_persistence._persistence_callback, "force_save_customer_state") as mock_save:
            agent_with_persistence.update_customer_state(updates)

            # Should update in-memory state
            assert agent_with_persistence.customer_state == updates

            # Should trigger persistence
            mock_save.assert_called_once_with(updates)

    def test_update_customer_state_multiple_updates(self, agent_without_persistence):
        """Test multiple customer state updates."""
        # First update
        agent_without_persistence.update_customer_state({"preference": "concise"})
        assert agent_without_persistence.customer_state == {"preference": "concise"}

        # Second update (should merge)
        agent_without_persistence.update_customer_state({"language": "en", "theme": "dark"})
        expected = {"preference": "concise", "language": "en", "theme": "dark"}
        assert agent_without_persistence.customer_state == expected

        # Third update (should override existing key)
        agent_without_persistence.update_customer_state({"preference": "verbose"})
        expected = {"preference": "verbose", "language": "en", "theme": "dark"}
        assert agent_without_persistence.customer_state == expected

    def test_update_customer_state_json_serializable_validation(self, agent_without_persistence):
        """Test that customer state updates must be JSON-serializable."""
        # Valid JSON-serializable data should work
        valid_updates = {
            "string": "value",
            "number": 42,
            "boolean": True,
            "null": None,
            "list": [1, 2, 3],
            "dict": {"nested": "value"},
        }
        agent_without_persistence.update_customer_state(valid_updates)
        assert agent_without_persistence.customer_state == valid_updates

        # Non-JSON-serializable data should raise TypeError
        class NonSerializable:
            pass

        invalid_updates = {"object": NonSerializable()}
        with pytest.raises(TypeError) as exc_info:
            agent_without_persistence.update_customer_state(invalid_updates)

        assert "must be JSON-serializable" in str(exc_info.value)

    def test_get_customer_state_returns_copy(self, agent_without_persistence):
        """Test that get_customer_state returns a copy to prevent accidental modification."""
        original_state = {"preference": "concise", "language": "en"}
        agent_without_persistence.update_customer_state(original_state)

        # Get state and modify the returned dict
        state_copy = agent_without_persistence.get_customer_state()
        state_copy["new_key"] = "new_value"

        # Original state should be unchanged
        assert agent_without_persistence.customer_state == original_state
        assert "new_key" not in agent_without_persistence.customer_state

    def test_clear_customer_state_without_persistence(self, agent_without_persistence):
        """Test clearing customer state without persistence."""
        # Set some initial state
        agent_without_persistence.update_customer_state({"preference": "concise", "language": "en"})
        assert agent_without_persistence.customer_state != {}

        # Clear state
        agent_without_persistence.clear_customer_state()

        assert agent_without_persistence.customer_state == {}
        assert agent_without_persistence.get_customer_state() == {}

    def test_clear_customer_state_with_persistence(self, agent_with_persistence):
        """Test clearing customer state with persistence."""
        # Set some initial state
        agent_with_persistence.update_customer_state({"preference": "concise"})

        # Mock the persistence callback method
        with patch.object(agent_with_persistence._persistence_callback, "force_save_customer_state") as mock_save:
            # Clear state
            agent_with_persistence.clear_customer_state()

            # Should clear in-memory state
            assert agent_with_persistence.customer_state == {}

            # Should trigger persistence of empty state
            mock_save.assert_called_with({})

    def test_clear_session_without_persistence(self, agent_without_persistence):
        """Test that clear_session raises ValueError when persistence is not enabled."""
        with pytest.raises(ValueError) as exc_info:
            agent_without_persistence.clear_session()

        assert "only available when persistence is enabled" in str(exc_info.value)

    def test_clear_session_with_persistence(self, agent_with_persistence, mock_persistence_manager):
        """Test clearing session with persistence."""
        # Set some initial state
        agent_with_persistence.messages = [{"role": "user", "content": [{"text": "Hello"}]}]
        agent_with_persistence.customer_state = {"preference": "concise"}

        # Clear session
        agent_with_persistence.clear_session()

        # Should delete from persistence
        mock_persistence_manager.delete_session.assert_called_once_with(
            "test_session", agent_with_persistence.agent_id, "test_user"
        )

        # Should clear in-memory state
        assert agent_with_persistence.messages == []
        assert agent_with_persistence.customer_state == {}

    @patch("strands.agent.agent.logger")
    def test_clear_session_logging(self, mock_logger, agent_with_persistence):
        """Test that clear_session logs the operation."""
        agent_with_persistence.clear_session()

        mock_logger.debug.assert_called()
        log_message = mock_logger.debug.call_args[0][0]
        assert "Cleared session" in log_message
        assert "test_session" in log_message
        assert "test_user" in log_message

    def test_clear_session_persistence_exception(self, agent_with_persistence, mock_persistence_manager):
        """Test that PersistenceException is propagated from clear_session."""
        mock_persistence_manager.delete_session.side_effect = PersistenceException("Delete failed")

        with pytest.raises(PersistenceException) as exc_info:
            agent_with_persistence.clear_session()

        assert "Delete failed" in str(exc_info.value)

    def test_update_customer_state_persistence_exception(self, agent_with_persistence):
        """Test that PersistenceException is propagated from update_customer_state."""
        # Mock the persistence callback to raise an exception
        with patch.object(agent_with_persistence._persistence_callback, "force_save_customer_state") as mock_save:
            mock_save.side_effect = PersistenceException("Save failed")

            with pytest.raises(PersistenceException) as exc_info:
                agent_with_persistence.update_customer_state({"key": "value"})

            assert "Save failed" in str(exc_info.value)

    def test_clear_customer_state_persistence_exception(self, agent_with_persistence):
        """Test that PersistenceException is propagated from clear_customer_state."""
        # Mock the persistence callback to raise an exception
        with patch.object(agent_with_persistence._persistence_callback, "force_save_customer_state") as mock_save:
            mock_save.side_effect = PersistenceException("Save failed")

            with pytest.raises(PersistenceException) as exc_info:
                agent_with_persistence.clear_customer_state()

            assert "Save failed" in str(exc_info.value)

    def test_customer_state_integration_with_restoration(self, mock_persistence_manager):
        """Test that customer state is properly restored during agent initialization."""
        # Setup mock to return existing customer state
        mock_persistence_manager.session_exists.return_value = True
        existing_state = {"preference": "verbose", "language": "es"}
        mock_persistence_manager.load_customer_state.return_value = existing_state

        agent = Agent(persistence_manager=mock_persistence_manager, session_id="test_session", user_id="test_user")

        # Should have restored the customer state
        assert agent.customer_state == existing_state
        assert agent.get_customer_state() == existing_state

    def test_customer_state_empty_dict_handling(self, agent_without_persistence):
        """Test handling of empty dictionary updates."""
        # Empty update should not cause issues
        agent_without_persistence.update_customer_state({})
        assert agent_without_persistence.customer_state == {}

        # Set some state, then update with empty dict (should not change anything)
        agent_without_persistence.update_customer_state({"key": "value"})
        agent_without_persistence.update_customer_state({})
        assert agent_without_persistence.customer_state == {"key": "value"}

    def test_customer_state_nested_data_structures(self, agent_without_persistence):
        """Test customer state with nested data structures."""
        complex_state = {
            "user_preferences": {
                "ui": {"theme": "dark", "language": "en"},
                "notifications": {"email": True, "push": False},
            },
            "history": ["action1", "action2", "action3"],
            "metadata": {"created": "2023-01-01", "version": 1.2},
        }

        agent_without_persistence.update_customer_state(complex_state)
        assert agent_without_persistence.customer_state == complex_state

        # Verify the returned copy is independent
        state_copy = agent_without_persistence.get_customer_state()
        state_copy["user_preferences"]["ui"]["theme"] = "light"

        # Original should be unchanged
        assert agent_without_persistence.customer_state["user_preferences"]["ui"]["theme"] == "dark"
