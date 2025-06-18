"""Tests for Agent class persistence integration."""

from unittest.mock import Mock, patch
import pytest

from strands.agent.agent import Agent
from strands.handlers.callback_handler import CompositeCallbackHandler
from strands.persistence.exceptions import PersistenceException
from strands.persistence.persistence_callback_handler import PersistenceCallbackHandler
from strands.persistence.persistence_manager import PersistenceManager


class TestAgentPersistenceIntegration:
    """Test Agent class integration with persistence functionality."""

    @pytest.fixture
    def mock_persistence_manager(self):
        """Create a mock persistence manager for testing."""
        mock_manager = Mock(spec=PersistenceManager)
        mock_manager.session_exists.return_value = False
        mock_manager.load_agent_state.return_value = []
        mock_manager.load_customer_state.return_value = {}
        mock_manager.load_request_state.return_value = None
        return mock_manager

    def test_agent_init_without_persistence(self):
        """Test agent initialization without persistence manager."""
        agent = Agent()

        assert agent.persistence_manager is None
        assert agent.session_id is None
        assert agent.user_id is None
        assert agent.agent_id.startswith("agent_")
        assert agent.customer_state == {}
        assert agent._persistence_callback is None

    def test_agent_init_with_persistence_valid_params(self, mock_persistence_manager):
        """Test agent initialization with valid persistence parameters."""
        agent = Agent(
            persistence_manager=mock_persistence_manager,
            session_id="test_session",
            agent_id="test_agent",
            user_id="test_user",
        )

        assert agent.persistence_manager == mock_persistence_manager
        assert agent.session_id == "test_session"
        assert agent.agent_id == "test_agent"
        assert agent.user_id == "test_user"
        assert agent.customer_state == {}
        assert agent._persistence_callback is not None
        assert isinstance(agent._persistence_callback, PersistenceCallbackHandler)

    def test_agent_init_with_persistence_auto_agent_id(self, mock_persistence_manager):
        """Test agent initialization with auto-generated agent_id."""
        agent = Agent(persistence_manager=mock_persistence_manager, session_id="test_session", user_id="test_user")

        assert agent.agent_id.startswith("agent_")
        assert len(agent.agent_id) == 14  # "agent_" + 8 hex chars

    def test_agent_init_persistence_missing_session_id(self, mock_persistence_manager):
        """Test that ValueError is raised when session_id is missing."""
        with pytest.raises(ValueError) as exc_info:
            Agent(persistence_manager=mock_persistence_manager, user_id="test_user")

        assert "session_id and user_id are required" in str(exc_info.value)

    def test_agent_init_persistence_missing_user_id(self, mock_persistence_manager):
        """Test that ValueError is raised when user_id is missing."""
        with pytest.raises(ValueError) as exc_info:
            Agent(persistence_manager=mock_persistence_manager, session_id="test_session")

        assert "session_id and user_id are required" in str(exc_info.value)

    def test_agent_init_callback_handler_composition(self, mock_persistence_manager):
        """Test that persistence callback is properly composed with existing callback handler."""
        agent = Agent(persistence_manager=mock_persistence_manager, session_id="test_session", user_id="test_user")

        # Should be a CompositeCallbackHandler
        assert isinstance(agent.callback_handler, CompositeCallbackHandler)

        # Should have both the original callback and persistence callback
        assert len(agent.callback_handler.handlers) == 2

    def test_agent_init_with_custom_callback_handler(self, mock_persistence_manager):
        """Test persistence integration with custom callback handler."""
        custom_callback = Mock()

        agent = Agent(
            persistence_manager=mock_persistence_manager,
            session_id="test_session",
            user_id="test_user",
            callback_handler=custom_callback,
        )

        # Should still be a CompositeCallbackHandler
        assert isinstance(agent.callback_handler, CompositeCallbackHandler)

        # Should include both custom callback and persistence callback
        assert len(agent.callback_handler.handlers) == 2
        assert custom_callback in agent.callback_handler.handlers

    def test_restore_persisted_state_no_existing_session(self, mock_persistence_manager):
        """Test state restoration when no existing session exists."""
        mock_persistence_manager.session_exists.return_value = False

        agent = Agent(persistence_manager=mock_persistence_manager, session_id="test_session", user_id="test_user")

        # Should not attempt to load state
        mock_persistence_manager.load_agent_state.assert_not_called()
        mock_persistence_manager.load_customer_state.assert_not_called()

        # Should have empty state
        assert agent.messages == []
        assert agent.customer_state == {}

    def test_restore_persisted_state_existing_session(self, mock_persistence_manager):
        """Test state restoration when existing session exists."""
        # Setup mock to return existing session data
        mock_persistence_manager.session_exists.return_value = True
        mock_messages = [
            {"role": "user", "content": [{"text": "Hello"}]},
            {"role": "assistant", "content": [{"text": "Hi there!"}]},
        ]
        mock_customer_state = {"preference": "concise", "language": "en"}

        mock_persistence_manager.load_agent_state.return_value = mock_messages
        mock_persistence_manager.load_customer_state.return_value = mock_customer_state

        agent = Agent(persistence_manager=mock_persistence_manager, session_id="test_session", user_id="test_user")

        # Should have restored state
        assert agent.messages == mock_messages
        assert agent.customer_state == mock_customer_state

        # Should have called load methods
        mock_persistence_manager.load_agent_state.assert_called_once_with("test_session", agent.agent_id, "test_user")
        mock_persistence_manager.load_customer_state.assert_called_once_with(
            "test_session", agent.agent_id, "test_user"
        )

    def test_restore_persisted_state_with_initial_messages(self, mock_persistence_manager):
        """Test that initial messages are not overridden by persisted state."""
        mock_persistence_manager.session_exists.return_value = True
        mock_persistence_manager.load_agent_state.return_value = [
            {"role": "user", "content": [{"text": "Persisted message"}]}
        ]

        initial_messages = [{"role": "user", "content": [{"text": "Initial message"}]}]

        agent = Agent(
            persistence_manager=mock_persistence_manager,
            session_id="test_session",
            user_id="test_user",
            messages=initial_messages,
        )

        # Should keep initial messages, not load persisted ones
        assert agent.messages == initial_messages
        mock_persistence_manager.load_agent_state.assert_not_called()

    def test_restore_persisted_state_persistence_exception(self, mock_persistence_manager):
        """Test that PersistenceException is re-raised during state restoration."""
        mock_persistence_manager.session_exists.return_value = True
        mock_persistence_manager.load_agent_state.side_effect = PersistenceException("Load failed")

        with pytest.raises(PersistenceException) as exc_info:
            Agent(persistence_manager=mock_persistence_manager, session_id="test_session", user_id="test_user")

        assert "Load failed" in str(exc_info.value)

    def test_restore_persisted_state_generic_exception(self, mock_persistence_manager):
        """Test that generic exceptions are wrapped in PersistenceException."""
        mock_persistence_manager.session_exists.return_value = True
        mock_persistence_manager.load_agent_state.side_effect = ValueError("Generic error")

        with pytest.raises(PersistenceException) as exc_info:
            Agent(persistence_manager=mock_persistence_manager, session_id="test_session", user_id="test_user")

        assert "Failed to restore persisted state" in str(exc_info.value)
        assert exc_info.value.cause.__class__ == ValueError

    def test_persistence_callback_handler_session_info(self, mock_persistence_manager):
        """Test that persistence callback handler has correct session info."""
        agent = Agent(
            persistence_manager=mock_persistence_manager,
            session_id="test_session",
            agent_id="test_agent",
            user_id="test_user",
        )

        session_info = agent._persistence_callback.get_session_info()
        expected = {"session_id": "test_session", "agent_id": "test_agent", "user_id": "test_user"}
        assert session_info == expected

    @patch("strands.agent.agent.logger")
    def test_restore_persisted_state_logging(self, mock_logger, mock_persistence_manager):
        """Test that state restoration logs appropriate messages."""
        # Test no existing session
        mock_persistence_manager.session_exists.return_value = False

        agent = Agent(persistence_manager=mock_persistence_manager, session_id="test_session", user_id="test_user")

        # Check that debug was called with a message about no existing session
        mock_logger.debug.assert_called_once()
        call_args = mock_logger.debug.call_args[0][0]
        assert call_args.startswith("No existing session found for test_session_")
        assert call_args.endswith("_test_user")

    @patch("strands.agent.agent.logger")
    def test_restore_persisted_state_logging_success(self, mock_logger, mock_persistence_manager):
        """Test logging on successful state restoration."""
        mock_persistence_manager.session_exists.return_value = True
        mock_messages = [{"role": "user", "content": [{"text": "Hello"}]}]
        mock_customer_state = {"preference": "concise"}

        mock_persistence_manager.load_agent_state.return_value = mock_messages
        mock_persistence_manager.load_customer_state.return_value = mock_customer_state

        Agent(persistence_manager=mock_persistence_manager, session_id="test_session", user_id="test_user")

        # Should log successful restoration
        debug_calls = [call[0][0] for call in mock_logger.debug.call_args_list]
        assert any("Restored 1 messages from persistence" in call for call in debug_calls)
        assert any("Restored customer state from persistence" in call for call in debug_calls)
