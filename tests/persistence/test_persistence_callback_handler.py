"""Tests for PersistenceCallbackHandler."""

from unittest.mock import Mock, patch
import pytest

from strands.persistence.persistence_callback_handler import PersistenceCallbackHandler
from strands.persistence.persistence_manager import PersistenceManager
from strands.telemetry.metrics import EventLoopMetrics


class TestPersistenceCallbackHandler:
    """Test the PersistenceCallbackHandler implementation."""

    @pytest.fixture
    def mock_persistence_manager(self):
        """Create a mock persistence manager for testing."""
        return Mock(spec=PersistenceManager)

    @pytest.fixture
    def handler(self, mock_persistence_manager):
        """Create a PersistenceCallbackHandler instance for testing."""
        return PersistenceCallbackHandler(
            persistence_manager=mock_persistence_manager,
            session_id="test_session",
            agent_id="test_agent",
            user_id="test_user",
        )

    @pytest.fixture
    def sample_messages(self):
        """Sample messages for testing."""
        return [
            {"role": "user", "content": [{"text": "Hello"}]},
            {"role": "assistant", "content": [{"text": "Hi there!"}]},
        ]

    @pytest.fixture
    def sample_customer_state(self):
        """Sample customer state for testing."""
        return {"preference": "concise", "language": "en"}

    @pytest.fixture
    def sample_metrics(self):
        """Sample EventLoopMetrics for testing."""
        return EventLoopMetrics(cycle_count=1, cycle_durations=[1.5])

    def test_init(self, mock_persistence_manager):
        """Test handler initialization."""
        handler = PersistenceCallbackHandler(
            persistence_manager=mock_persistence_manager, session_id="session1", agent_id="agent1", user_id="user1"
        )

        assert handler.persistence_manager == mock_persistence_manager
        assert handler.session_id == "session1"
        assert handler.agent_id == "agent1"
        assert handler.user_id == "user1"
        assert handler._last_saved_messages_count == 0
        assert handler._last_saved_customer_state_hash is None

    def test_handle_message_persistence_with_messages_list(self, handler, mock_persistence_manager, sample_messages):
        """Test message persistence when messages list is provided."""
        handler(messages=sample_messages)

        mock_persistence_manager.save_agent_state.assert_called_once_with(
            "test_session", "test_agent", "test_user", sample_messages
        )
        assert handler._last_saved_messages_count == len(sample_messages)

    def test_handle_message_persistence_with_message_list(self, handler, mock_persistence_manager, sample_messages):
        """Test message persistence with alternative message_list parameter."""
        handler(message=sample_messages[0], message_list=sample_messages)

        mock_persistence_manager.save_agent_state.assert_called_once_with(
            "test_session", "test_agent", "test_user", sample_messages
        )
        assert handler._last_saved_messages_count == len(sample_messages)

    def test_handle_message_persistence_no_redundant_saves(self, handler, mock_persistence_manager, sample_messages):
        """Test that redundant message saves are avoided."""
        # First call should save
        handler(messages=sample_messages)
        assert mock_persistence_manager.save_agent_state.call_count == 1

        # Second call with same messages should not save
        handler(messages=sample_messages)
        assert mock_persistence_manager.save_agent_state.call_count == 1

        # Call with more messages should save
        extended_messages = sample_messages + [{"role": "user", "content": [{"text": "More"}]}]
        handler(messages=extended_messages)
        assert mock_persistence_manager.save_agent_state.call_count == 2

    def test_handle_customer_state_persistence(self, handler, mock_persistence_manager, sample_customer_state):
        """Test customer state persistence."""
        handler(customer_state=sample_customer_state)

        mock_persistence_manager.save_customer_state.assert_called_once_with(
            "test_session", "test_agent", "test_user", sample_customer_state
        )

    def test_handle_customer_state_persistence_no_redundant_saves(
        self, handler, mock_persistence_manager, sample_customer_state
    ):
        """Test that redundant customer state saves are avoided."""
        # First call should save
        handler(customer_state=sample_customer_state)
        assert mock_persistence_manager.save_customer_state.call_count == 1

        # Second call with same state should not save
        handler(customer_state=sample_customer_state)
        assert mock_persistence_manager.save_customer_state.call_count == 1

        # Call with different state should save
        different_state = {"preference": "verbose", "language": "en"}
        handler(customer_state=different_state)
        assert mock_persistence_manager.save_customer_state.call_count == 2

    def test_handle_request_state_persistence(self, handler, mock_persistence_manager, sample_messages, sample_metrics):
        """Test request state persistence."""
        latest_message = sample_messages[0]
        stop_reason = "end_turn"

        handler(latest_message=latest_message, event_loop_metrics=sample_metrics, stop_reason=stop_reason)

        mock_persistence_manager.save_request_state.assert_called_once_with(
            "test_session", "test_agent", "test_user", latest_message, sample_metrics, stop_reason
        )

    def test_handle_request_state_persistence_missing_data(self, handler, mock_persistence_manager):
        """Test that request state persistence is skipped when data is incomplete."""
        # Missing stop_reason
        handler(
            latest_message={"role": "assistant", "content": [{"text": "test"}]}, event_loop_metrics=EventLoopMetrics()
        )

        mock_persistence_manager.save_request_state.assert_not_called()

    def test_handle_request_state_persistence_invalid_types(self, handler, mock_persistence_manager):
        """Test that request state persistence is skipped with invalid data types."""
        handler(
            latest_message="not a dict",  # Invalid type
            event_loop_metrics=EventLoopMetrics(),
            stop_reason="end_turn",
        )

        mock_persistence_manager.save_request_state.assert_not_called()

    def test_multiple_persistence_operations_in_single_call(
        self, handler, mock_persistence_manager, sample_messages, sample_customer_state, sample_metrics
    ):
        """Test handling multiple persistence operations in a single callback."""
        latest_message = sample_messages[0]
        stop_reason = "end_turn"

        handler(
            messages=sample_messages,
            customer_state=sample_customer_state,
            latest_message=latest_message,
            event_loop_metrics=sample_metrics,
            stop_reason=stop_reason,
        )

        # All three persistence operations should be called
        mock_persistence_manager.save_agent_state.assert_called_once()
        mock_persistence_manager.save_customer_state.assert_called_once()
        mock_persistence_manager.save_request_state.assert_called_once()

    @patch("strands.persistence.persistence_callback_handler.logger")
    def test_persistence_error_handling(self, mock_logger, handler, mock_persistence_manager, sample_messages):
        """Test that persistence errors are logged but don't break execution."""
        # Make persistence manager raise an exception
        mock_persistence_manager.save_agent_state.side_effect = Exception("Persistence failed")

        # Should not raise exception
        handler(messages=sample_messages)

        # Should log the error
        mock_logger.error.assert_called_once()
        assert "Persistence operation failed" in str(mock_logger.error.call_args)

    def test_force_save_agent_state(self, handler, mock_persistence_manager, sample_messages):
        """Test force save agent state method."""
        handler.force_save_agent_state(sample_messages)

        mock_persistence_manager.save_agent_state.assert_called_once_with(
            "test_session", "test_agent", "test_user", sample_messages
        )
        assert handler._last_saved_messages_count == len(sample_messages)

    @patch("strands.persistence.persistence_callback_handler.logger")
    def test_force_save_agent_state_error_handling(
        self, mock_logger, handler, mock_persistence_manager, sample_messages
    ):
        """Test error handling in force save agent state."""
        mock_persistence_manager.save_agent_state.side_effect = Exception("Save failed")

        handler.force_save_agent_state(sample_messages)

        mock_logger.error.assert_called_once()
        assert "Force save agent state failed" in str(mock_logger.error.call_args)

    def test_force_save_customer_state(self, handler, mock_persistence_manager, sample_customer_state):
        """Test force save customer state method."""
        handler.force_save_customer_state(sample_customer_state)

        mock_persistence_manager.save_customer_state.assert_called_once_with(
            "test_session", "test_agent", "test_user", sample_customer_state
        )

    @patch("strands.persistence.persistence_callback_handler.logger")
    def test_force_save_customer_state_error_handling(
        self, mock_logger, handler, mock_persistence_manager, sample_customer_state
    ):
        """Test error handling in force save customer state."""
        mock_persistence_manager.save_customer_state.side_effect = Exception("Save failed")

        handler.force_save_customer_state(sample_customer_state)

        mock_logger.error.assert_called_once()
        assert "Force save customer state failed" in str(mock_logger.error.call_args)

    def test_force_save_request_state(self, handler, mock_persistence_manager, sample_messages, sample_metrics):
        """Test force save request state method."""
        message = sample_messages[0]
        stop_reason = "end_turn"

        handler.force_save_request_state(message, sample_metrics, stop_reason)

        mock_persistence_manager.save_request_state.assert_called_once_with(
            "test_session", "test_agent", "test_user", message, sample_metrics, stop_reason
        )

    @patch("strands.persistence.persistence_callback_handler.logger")
    def test_force_save_request_state_error_handling(
        self, mock_logger, handler, mock_persistence_manager, sample_messages, sample_metrics
    ):
        """Test error handling in force save request state."""
        mock_persistence_manager.save_request_state.side_effect = Exception("Save failed")

        message = sample_messages[0]
        stop_reason = "end_turn"

        handler.force_save_request_state(message, sample_metrics, stop_reason)

        mock_logger.error.assert_called_once()
        assert "Force save request state failed" in str(mock_logger.error.call_args)

    def test_get_session_info(self, handler):
        """Test getting session information."""
        session_info = handler.get_session_info()

        expected = {"session_id": "test_session", "agent_id": "test_agent", "user_id": "test_user"}
        assert session_info == expected

    def test_callback_with_irrelevant_data(self, handler, mock_persistence_manager):
        """Test that callback ignores irrelevant data."""
        handler(irrelevant_key="irrelevant_value", another_key=123, random_data={"key": "value"})

        # No persistence operations should be called
        mock_persistence_manager.save_agent_state.assert_not_called()
        mock_persistence_manager.save_customer_state.assert_not_called()
        mock_persistence_manager.save_request_state.assert_not_called()

    def test_callback_with_invalid_message_types(self, handler, mock_persistence_manager):
        """Test that callback handles invalid message types gracefully."""
        handler(
            messages="not a list",  # Invalid type
            customer_state="not a dict",  # Invalid type
        )

        # No persistence operations should be called
        mock_persistence_manager.save_agent_state.assert_not_called()
        mock_persistence_manager.save_customer_state.assert_not_called()
