"""Tests for FilePersistenceManager."""

import json
import os
import tempfile
import shutil
from unittest.mock import patch, mock_open

import pytest

from strands.persistence.file_persistence_manager import FilePersistenceManager
from strands.persistence.exceptions import PersistenceException
from strands.telemetry.metrics import EventLoopMetrics
from strands.types.content import Message


class TestFilePersistenceManager:
    """Test the FilePersistenceManager implementation."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def manager(self, temp_dir):
        """Create a FilePersistenceManager instance for testing."""
        return FilePersistenceManager(storage_dir=temp_dir)

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
        return {"preference": "concise", "language": "en", "settings": {"theme": "dark"}}

    @pytest.fixture
    def sample_metrics(self):
        """Sample EventLoopMetrics for testing."""
        return EventLoopMetrics(
            cycle_count=1,
            cycle_durations=[1.5],
            accumulated_usage={"inputTokens": 10, "outputTokens": 20, "totalTokens": 30},
        )

    def test_init_with_default_storage_dir(self):
        """Test initialization with default storage directory."""
        manager = FilePersistenceManager()
        assert manager.storage_dir == tempfile.gettempdir()
        assert os.path.exists(manager.storage_dir)

    def test_init_with_custom_storage_dir(self, temp_dir):
        """Test initialization with custom storage directory."""
        manager = FilePersistenceManager(storage_dir=temp_dir)
        assert manager.storage_dir == temp_dir
        assert os.path.exists(temp_dir)

    def test_init_creates_storage_dir_if_not_exists(self):
        """Test that initialization creates storage directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage_dir = os.path.join(temp_dir, "new_storage")
            assert not os.path.exists(storage_dir)

            manager = FilePersistenceManager(storage_dir=storage_dir)
            assert os.path.exists(storage_dir)

    @patch("os.makedirs")
    def test_init_raises_exception_on_dir_creation_failure(self, mock_makedirs):
        """Test that initialization raises PersistenceException if directory creation fails."""
        mock_makedirs.side_effect = OSError("Permission denied")

        with pytest.raises(PersistenceException) as exc_info:
            FilePersistenceManager(storage_dir="/invalid/path")

        assert "Failed to create storage directory" in str(exc_info.value)

    def test_get_session_dir(self, manager):
        """Test session directory path generation."""
        session_dir = manager._get_session_dir("session1", "agent1", "user1")
        expected = os.path.join(manager.storage_dir, "session1_agent1_user1")
        assert session_dir == expected

    def test_ensure_session_dir_creates_directory(self, manager):
        """Test that _ensure_session_dir creates the session directory."""
        session_dir = manager._ensure_session_dir("session1", "agent1", "user1")
        assert os.path.exists(session_dir)
        assert session_dir.endswith("session1_agent1_user1")

    def test_save_agent_state(self, manager, sample_messages):
        """Test saving agent state to file."""
        manager.save_agent_state("session1", "agent1", "user1", sample_messages)

        # Verify file was created
        session_dir = manager._get_session_dir("session1", "agent1", "user1")
        file_path = os.path.join(session_dir, "agent_state.json")
        assert os.path.exists(file_path)

        # Verify content
        with open(file_path, "r") as f:
            saved_data = json.load(f)
        assert saved_data == sample_messages

    def test_save_customer_state(self, manager, sample_customer_state):
        """Test saving customer state to file."""
        manager.save_customer_state("session1", "agent1", "user1", sample_customer_state)

        # Verify file was created
        session_dir = manager._get_session_dir("session1", "agent1", "user1")
        file_path = os.path.join(session_dir, "customer_state.json")
        assert os.path.exists(file_path)

        # Verify content
        with open(file_path, "r") as f:
            saved_data = json.load(f)
        assert saved_data == sample_customer_state

    def test_save_request_state(self, manager, sample_messages, sample_metrics):
        """Test saving request state to file."""
        message = sample_messages[0]
        stop_reason = "end_turn"

        manager.save_request_state("session1", "agent1", "user1", message, sample_metrics, stop_reason)

        # Verify file was created
        session_dir = manager._get_session_dir("session1", "agent1", "user1")
        file_path = os.path.join(session_dir, "request_state.json")
        assert os.path.exists(file_path)

        # Verify content structure
        with open(file_path, "r") as f:
            saved_data = json.load(f)

        assert "message" in saved_data
        assert "metrics" in saved_data
        assert "stop_reason" in saved_data
        assert saved_data["message"] == message
        assert saved_data["stop_reason"] == stop_reason

    def test_load_agent_state_existing(self, manager, sample_messages):
        """Test loading existing agent state."""
        # Save first
        manager.save_agent_state("session1", "agent1", "user1", sample_messages)

        # Load and verify
        loaded_messages = manager.load_agent_state("session1", "agent1", "user1")
        assert loaded_messages == sample_messages

    def test_load_agent_state_nonexistent(self, manager):
        """Test loading agent state when file doesn't exist."""
        loaded_messages = manager.load_agent_state("nonexistent", "agent1", "user1")
        assert loaded_messages == []

    def test_load_customer_state_existing(self, manager, sample_customer_state):
        """Test loading existing customer state."""
        # Save first
        manager.save_customer_state("session1", "agent1", "user1", sample_customer_state)

        # Load and verify
        loaded_state = manager.load_customer_state("session1", "agent1", "user1")
        assert loaded_state == sample_customer_state

    def test_load_customer_state_nonexistent(self, manager):
        """Test loading customer state when file doesn't exist."""
        loaded_state = manager.load_customer_state("nonexistent", "agent1", "user1")
        assert loaded_state == {}

    def test_load_request_state_existing(self, manager, sample_messages, sample_metrics):
        """Test loading existing request state."""
        message = sample_messages[0]
        stop_reason = "end_turn"

        # Save first
        manager.save_request_state("session1", "agent1", "user1", message, sample_metrics, stop_reason)

        # Load and verify
        loaded_state = manager.load_request_state("session1", "agent1", "user1")
        assert loaded_state is not None

        loaded_message, loaded_metrics, loaded_stop_reason = loaded_state
        assert loaded_message == message
        assert loaded_stop_reason == stop_reason
        assert isinstance(loaded_metrics, EventLoopMetrics)

    def test_load_request_state_nonexistent(self, manager):
        """Test loading request state when file doesn't exist."""
        loaded_state = manager.load_request_state("nonexistent", "agent1", "user1")
        assert loaded_state is None

    def test_delete_session(self, manager, sample_messages, sample_customer_state):
        """Test deleting a session."""
        # Create session with data
        manager.save_agent_state("session1", "agent1", "user1", sample_messages)
        manager.save_customer_state("session1", "agent1", "user1", sample_customer_state)

        # Verify session exists
        assert manager.session_exists("session1", "agent1", "user1")

        # Delete session
        manager.delete_session("session1", "agent1", "user1")

        # Verify session no longer exists
        assert not manager.session_exists("session1", "agent1", "user1")
        session_dir = manager._get_session_dir("session1", "agent1", "user1")
        assert not os.path.exists(session_dir)

    def test_delete_nonexistent_session(self, manager):
        """Test deleting a session that doesn't exist."""
        # Should not raise an exception
        manager.delete_session("nonexistent", "agent1", "user1")

    def test_session_exists_true(self, manager, sample_messages):
        """Test session_exists returns True when session has data."""
        manager.save_agent_state("session1", "agent1", "user1", sample_messages)
        assert manager.session_exists("session1", "agent1", "user1")

    def test_session_exists_false(self, manager):
        """Test session_exists returns False when session has no data."""
        assert not manager.session_exists("nonexistent", "agent1", "user1")

    def test_session_exists_empty_directory(self, manager):
        """Test session_exists returns False for empty session directory."""
        # Create empty session directory
        session_dir = manager._ensure_session_dir("session1", "agent1", "user1")
        assert os.path.exists(session_dir)

        # Should return False since no data files exist
        assert not manager.session_exists("session1", "agent1", "user1")

    @patch("builtins.open", side_effect=OSError("Permission denied"))
    def test_save_operation_failure(self, mock_open, manager, sample_messages):
        """Test that save operations raise PersistenceException on file errors."""
        with pytest.raises(PersistenceException) as exc_info:
            manager.save_agent_state("session1", "agent1", "user1", sample_messages)

        assert "Failed to write file" in str(exc_info.value)

    def test_load_corrupted_json(self, manager):
        """Test loading corrupted JSON data raises PersistenceException."""
        # Create session directory and corrupted file
        session_dir = manager._ensure_session_dir("session1", "agent1", "user1")
        file_path = os.path.join(session_dir, "agent_state.json")

        with open(file_path, "w") as f:
            f.write("invalid json {")

        with pytest.raises(PersistenceException) as exc_info:
            manager.load_agent_state("session1", "agent1", "user1")

        assert "Corrupted JSON data" in str(exc_info.value)

    def test_load_invalid_request_state_format(self, manager):
        """Test loading request state with invalid format raises PersistenceException."""
        # Create session directory and invalid request state file
        session_dir = manager._ensure_session_dir("session1", "agent1", "user1")
        file_path = os.path.join(session_dir, "request_state.json")

        # Missing required fields
        invalid_data = {"message": "test"}
        with open(file_path, "w") as f:
            json.dump(invalid_data, f)

        with pytest.raises(PersistenceException) as exc_info:
            manager.load_request_state("session1", "agent1", "user1")

        assert "Invalid request state format" in str(exc_info.value)

    def test_atomic_write_operation(self, manager, sample_messages):
        """Test that write operations are atomic (use temporary files)."""
        with patch("os.replace") as mock_replace:
            manager.save_agent_state("session1", "agent1", "user1", sample_messages)

            # Verify os.replace was called (atomic operation)
            mock_replace.assert_called_once()

    def test_cleanup_temp_file_on_write_failure(self, manager, sample_messages):
        """Test that temporary files are cleaned up on write failure."""
        session_dir = manager._ensure_session_dir("session1", "agent1", "user1")
        file_path = os.path.join(session_dir, "agent_state.json")
        temp_path = file_path + ".tmp"

        with patch("os.replace", side_effect=OSError("Write failed")):
            with pytest.raises(PersistenceException):
                manager.save_agent_state("session1", "agent1", "user1", sample_messages)

            # Verify temp file doesn't exist after failure
            assert not os.path.exists(temp_path)
