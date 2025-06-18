"""Tests for Agent automatic state restoration functionality."""

from unittest.mock import Mock, patch
import pytest

from strands.agent.agent import Agent
from strands.persistence.exceptions import PersistenceException
from strands.persistence.persistence_manager import PersistenceManager
from strands.telemetry.metrics import EventLoopMetrics


class TestAgentStateRestoration:
    """Test Agent automatic state restoration functionality."""

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
    def sample_messages(self):
        """Sample messages for testing."""
        return [
            {"role": "user", "content": [{"text": "Hello"}]},
            {"role": "assistant", "content": [{"text": "Hi there!"}]},
            {"role": "user", "content": [{"text": "How are you?"}]},
        ]

    @pytest.fixture
    def sample_customer_state(self):
        """Sample customer state for testing."""
        return {"preference": "verbose", "language": "es", "settings": {"theme": "dark", "notifications": True}}

    @pytest.fixture
    def sample_request_state(self):
        """Sample request state for testing."""
        message = {"role": "assistant", "content": [{"text": "Test response"}]}
        metrics = EventLoopMetrics(cycle_count=2, cycle_durations=[1.0, 1.5])
        stop_reason = "end_turn"
        return (message, metrics, stop_reason)

    def test_automatic_restoration_no_existing_session(self, mock_persistence_manager):
        """Test automatic restoration when no existing session exists."""
        mock_persistence_manager.session_exists.return_value = False

        agent = Agent(persistence_manager=mock_persistence_manager, session_id="test_session", user_id="test_user")

        # Should not attempt to load any state
        mock_persistence_manager.load_agent_state.assert_not_called()
        mock_persistence_manager.load_customer_state.assert_not_called()

        # Should have default empty state
        assert agent.messages == []
        assert agent.customer_state == {}

    def test_automatic_restoration_existing_session(
        self, mock_persistence_manager, sample_messages, sample_customer_state
    ):
        """Test automatic restoration when existing session exists."""
        mock_persistence_manager.session_exists.return_value = True
        mock_persistence_manager.load_agent_state.return_value = sample_messages
        mock_persistence_manager.load_customer_state.return_value = sample_customer_state

        agent = Agent(persistence_manager=mock_persistence_manager, session_id="test_session", user_id="test_user")

        # Should have restored state
        assert agent.messages == sample_messages
        assert agent.customer_state == sample_customer_state

        # Should have called load methods
        mock_persistence_manager.load_agent_state.assert_called_once()
        mock_persistence_manager.load_customer_state.assert_called_once()

    def test_automatic_restoration_preserves_initial_messages(self, mock_persistence_manager, sample_messages):
        """Test that initial messages are preserved over persisted messages."""
        mock_persistence_manager.session_exists.return_value = True
        mock_persistence_manager.load_agent_state.return_value = sample_messages

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

    def test_restore_request_state_without_persistence(self):
        """Test that restore_request_state raises ValueError without persistence."""
        agent = Agent()

        with pytest.raises(ValueError) as exc_info:
            agent.restore_request_state()

        assert "only available when persistence is enabled" in str(exc_info.value)

    def test_restore_request_state_no_existing_state(self, mock_persistence_manager):
        """Test restore_request_state when no request state exists."""
        mock_persistence_manager.load_request_state.return_value = None

        agent = Agent(persistence_manager=mock_persistence_manager, session_id="test_session", user_id="test_user")

        result = agent.restore_request_state()
        assert result is None

    def test_restore_request_state_existing_state(self, mock_persistence_manager, sample_request_state):
        """Test restore_request_state with existing request state."""
        mock_persistence_manager.load_request_state.return_value = sample_request_state

        agent = Agent(persistence_manager=mock_persistence_manager, session_id="test_session", user_id="test_user")

        result = agent.restore_request_state()

        assert result is not None
        assert result["message"] == sample_request_state[0]
        assert result["stop_reason"] == sample_request_state[2]
        assert "metrics" in result
        assert isinstance(result["metrics"], dict)

    def test_restore_request_state_persistence_exception(self, mock_persistence_manager):
        """Test that PersistenceException is propagated from restore_request_state."""
        mock_persistence_manager.load_request_state.side_effect = PersistenceException("Load failed")

        agent = Agent(persistence_manager=mock_persistence_manager, session_id="test_session", user_id="test_user")

        with pytest.raises(PersistenceException) as exc_info:
            agent.restore_request_state()

        assert "Load failed" in str(exc_info.value)

    def test_force_restore_conversation_without_persistence(self):
        """Test that force_restore_conversation raises ValueError without persistence."""
        agent = Agent()

        with pytest.raises(ValueError) as exc_info:
            agent.force_restore_conversation()

        assert "only available when persistence is enabled" in str(exc_info.value)

    def test_force_restore_conversation_success(self, mock_persistence_manager, sample_messages):
        """Test successful force restore of conversation."""
        mock_persistence_manager.load_agent_state.return_value = sample_messages

        agent = Agent(persistence_manager=mock_persistence_manager, session_id="test_session", user_id="test_user")

        # Set some initial messages that should be replaced
        agent.messages = [{"role": "user", "content": [{"text": "Old message"}]}]

        restored_count = agent.force_restore_conversation()

        assert restored_count == len(sample_messages)
        assert agent.messages == sample_messages

    @patch("strands.agent.agent.logger")
    def test_force_restore_conversation_logging(self, mock_logger, mock_persistence_manager, sample_messages):
        """Test that force_restore_conversation logs the operation."""
        mock_persistence_manager.load_agent_state.return_value = sample_messages

        agent = Agent(persistence_manager=mock_persistence_manager, session_id="test_session", user_id="test_user")

        agent.force_restore_conversation()

        mock_logger.debug.assert_called()
        log_message = mock_logger.debug.call_args[0][0]
        assert "Force restored" in log_message
        assert str(len(sample_messages)) in log_message

    def test_force_restore_conversation_persistence_exception(self, mock_persistence_manager):
        """Test that PersistenceException is propagated from force_restore_conversation."""
        mock_persistence_manager.load_agent_state.side_effect = PersistenceException("Load failed")

        agent = Agent(persistence_manager=mock_persistence_manager, session_id="test_session", user_id="test_user")

        with pytest.raises(PersistenceException) as exc_info:
            agent.force_restore_conversation()

        assert "Load failed" in str(exc_info.value)

    def test_force_restore_customer_state_without_persistence(self):
        """Test that force_restore_customer_state raises ValueError without persistence."""
        agent = Agent()

        with pytest.raises(ValueError) as exc_info:
            agent.force_restore_customer_state()

        assert "only available when persistence is enabled" in str(exc_info.value)

    def test_force_restore_customer_state_success(self, mock_persistence_manager, sample_customer_state):
        """Test successful force restore of customer state."""
        mock_persistence_manager.load_customer_state.return_value = sample_customer_state

        agent = Agent(persistence_manager=mock_persistence_manager, session_id="test_session", user_id="test_user")

        # Set some initial state that should be replaced
        agent.customer_state = {"old_key": "old_value"}

        restored_state = agent.force_restore_customer_state()

        assert restored_state == sample_customer_state
        assert agent.customer_state == sample_customer_state

    @patch("strands.agent.agent.logger")
    def test_force_restore_customer_state_logging(self, mock_logger, mock_persistence_manager, sample_customer_state):
        """Test that force_restore_customer_state logs the operation."""
        mock_persistence_manager.load_customer_state.return_value = sample_customer_state

        agent = Agent(persistence_manager=mock_persistence_manager, session_id="test_session", user_id="test_user")

        agent.force_restore_customer_state()

        mock_logger.debug.assert_called()
        log_message = mock_logger.debug.call_args[0][0]
        assert "Force restored customer state" in log_message

    def test_force_restore_customer_state_persistence_exception(self, mock_persistence_manager):
        """Test that PersistenceException is propagated from force_restore_customer_state."""
        mock_persistence_manager.load_customer_state.side_effect = PersistenceException("Load failed")

        agent = Agent(persistence_manager=mock_persistence_manager, session_id="test_session", user_id="test_user")

        with pytest.raises(PersistenceException) as exc_info:
            agent.force_restore_customer_state()

        assert "Load failed" in str(exc_info.value)

    def test_restoration_with_generic_exception_wrapping(self, mock_persistence_manager):
        """Test that generic exceptions are wrapped in PersistenceException during restoration."""
        mock_persistence_manager.session_exists.return_value = True
        mock_persistence_manager.load_agent_state.side_effect = ValueError("Generic error")

        with pytest.raises(PersistenceException) as exc_info:
            Agent(persistence_manager=mock_persistence_manager, session_id="test_session", user_id="test_user")

        assert "Failed to restore persisted state" in str(exc_info.value)
        assert exc_info.value.cause.__class__ == ValueError

    def test_restoration_methods_return_copies(self, mock_persistence_manager, sample_customer_state):
        """Test that restoration methods return copies to prevent accidental modification."""
        mock_persistence_manager.load_customer_state.return_value = sample_customer_state

        agent = Agent(persistence_manager=mock_persistence_manager, session_id="test_session", user_id="test_user")

        restored_state = agent.force_restore_customer_state()

        # Modify the returned copy
        restored_state["new_key"] = "new_value"

        # Original agent state should be unchanged
        assert "new_key" not in agent.customer_state

    def test_multiple_restoration_calls(self, mock_persistence_manager, sample_messages, sample_customer_state):
        """Test multiple restoration calls work correctly."""
        mock_persistence_manager.load_agent_state.return_value = sample_messages
        mock_persistence_manager.load_customer_state.return_value = sample_customer_state

        agent = Agent(persistence_manager=mock_persistence_manager, session_id="test_session", user_id="test_user")

        # First restoration
        count1 = agent.force_restore_conversation()
        state1 = agent.force_restore_customer_state()

        # Second restoration (should work the same)
        count2 = agent.force_restore_conversation()
        state2 = agent.force_restore_customer_state()

        assert count1 == count2 == len(sample_messages)
        assert state1 == state2 == sample_customer_state
        assert agent.messages == sample_messages
        assert agent.customer_state == sample_customer_state
