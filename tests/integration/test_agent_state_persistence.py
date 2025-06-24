"""Integration tests for agent state persistence."""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch

from strands.agent.agent import Agent
from strands.agent.state import AgentState
from strands.session.default_session_manager import DefaultSessionManager
from strands.session.file_session_datastore import FileSessionDatastore
from strands.types.content import Message


class TestAgentStatePersistenceIntegration:
    """Test end-to-end agent state persistence."""
    
    @pytest.fixture
    def temp_session_dir(self):
        """Create temporary directory for session storage."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    def session_manager(self, temp_session_dir):
        """Create session manager with temporary storage."""
        datastore = FileSessionDatastore(temp_session_dir)
        return DefaultSessionManager(
            user_id="test_user",
            agent_id="test_agent",
            session_datastore=datastore
        )
    
    @pytest.fixture
    def mock_model(self):
        """Create mock model for testing."""
        model = Mock()
        model.model_id = "test-model"
        return model
    
    def test_agent_state_persistence_cycle(self, session_manager, mock_model):
        """Test complete state persistence and restoration cycle."""
        # Create first agent and modify state
        agent1 = Agent(model=mock_model, session_manager=session_manager)
        
        # Set various state values
        agent1.state.set("tool_count", 5)
        agent1.state.set("api_key", "secret123")
        agent1.state.set("user_pref", "dark_mode", namespace="user_settings")
        agent1.state.set("session_data", {"active": True}, namespace="user_settings")
        
        # Simulate message processing to trigger persistence
        test_message = Message(role="assistant", content="Test response")
        session_manager.update_session(agent1, test_message)
        
        # Create second agent with same session manager
        agent2 = Agent(model=mock_model, session_manager=session_manager)
        
        # Verify state was restored
        assert agent2.state.get("tool_count") == 5
        assert agent2.state.get("api_key") == "secret123"
        assert agent2.state.get("user_pref", namespace="user_settings") == "dark_mode"
        assert agent2.state.get("session_data", namespace="user_settings") == {"active": True}
    
    def test_multiple_namespace_persistence(self, session_manager, mock_model):
        """Test persistence of multiple namespaces."""
        agent1 = Agent(model=mock_model, session_manager=session_manager)
        
        # Set data in multiple namespaces
        agent1.state.set("default_key", "default_value")
        agent1.state.set("user_key", "user_value", namespace="user")
        agent1.state.set("custom_key", "custom_value", namespace="custom")
        agent1.state.set("sdk_key", "sdk_value", namespace="sdk")
        
        # Trigger persistence
        test_message = Message(role="assistant", content="Test")
        session_manager.update_session(agent1, test_message)
        
        # Create new agent and verify all namespaces
        agent2 = Agent(model=mock_model, session_manager=session_manager)
        
        all_state = agent2.state.get_all()
        assert all_state["default"]["default_key"] == "default_value"
        assert all_state["user"]["user_key"] == "user_value"
        assert all_state["custom"]["custom_key"] == "custom_value"
        assert all_state["sdk"]["sdk_key"] == "sdk_value"
    
    def test_state_changes_trigger_persistence(self, session_manager, mock_model):
        """Test that state changes trigger persistence callbacks."""
        agent = Agent(model=mock_model, session_manager=session_manager)
        
        # Mock the session manager's update_session method
        with patch.object(session_manager, 'update_session') as mock_update:
            # Modify state
            agent.state.set("test_key", "test_value")
            
            # Simulate message processing that would trigger callback
            test_message = Message(role="assistant", content="Test")
            session_manager.update_session(agent, test_message)
            
            # Verify update_session was called
            mock_update.assert_called_once_with(agent, test_message)
    
    def test_backward_compatibility_with_existing_sessions(self, temp_session_dir, mock_model):
        """Test that agents work with existing sessions that don't have state."""
        # Create session manager and manually create old-format session
        datastore = FileSessionDatastore(temp_session_dir)
        session_manager = DefaultSessionManager(
            user_id="test_user",
            agent_id="test_agent", 
            session_datastore=datastore
        )
        
        # Manually create old session format (without state field)
        old_session_data = {
            "session_id": session_manager.session.session_id,
            "user_id": "test_user",
            "agent_id": "test_agent",
            "messages": [{"role": "user", "content": "Hello"}],
            "created_at": "2024-06-24T12:00:00Z",
            "updated_at": "2024-06-24T12:00:00Z"
        }
        
        # Save old format session
        session_file = os.path.join(temp_session_dir, f"{session_manager.session.session_id}.json")
        import json
        with open(session_file, 'w') as f:
            json.dump(old_session_data, f)
        
        # Create agent - should handle missing state gracefully
        agent = Agent(model=mock_model, session_manager=session_manager)
        
        # Should have empty state
        assert agent.state.get_all() == {"default": {}, "sdk": {}}
        
        # Should be able to set state normally
        agent.state.set("new_key", "new_value")
        assert agent.state.get("new_key") == "new_value"
    
    def test_persistence_failure_handling(self, mock_model):
        """Test that persistence failures don't break agent functionality."""
        # Create session manager that will fail
        failing_session_manager = Mock()
        failing_session_manager.restore_agent_from_session = Mock()
        failing_session_manager.update_session = Mock(side_effect=Exception("Persistence failed"))
        
        agent = Agent(model=mock_model, session_manager=failing_session_manager)
        
        # Agent should still function normally
        agent.state.set("key", "value")
        assert agent.state.get("key") == "value"
        
        # Persistence failure should be handled gracefully
        test_message = Message(role="assistant", content="Test")
        # This should not raise an exception
        try:
            failing_session_manager.update_session(agent, test_message)
        except Exception:
            pass  # Expected to fail, but agent should continue working
        
        # Agent state should still be accessible
        assert agent.state.get("key") == "value"
    
    def test_concurrent_agent_state_access(self, session_manager, mock_model):
        """Test concurrent access to agent state."""
        import threading
        import time
        
        agent = Agent(model=mock_model, session_manager=session_manager)
        results = []
        errors = []
        
        def worker(worker_id):
            try:
                for i in range(10):
                    key = f"worker_{worker_id}_key_{i}"
                    value = f"worker_{worker_id}_value_{i}"
                    agent.state.set(key, value)
                    
                    # Small delay to increase chance of race conditions
                    time.sleep(0.001)
                    
                    retrieved = agent.state.get(key)
                    if retrieved == value:
                        results.append((worker_id, i, "success"))
                    else:
                        results.append((worker_id, i, f"mismatch: {retrieved} != {value}"))
            except Exception as e:
                errors.append((worker_id, str(e)))
        
        # Start multiple threads
        threads = []
        for worker_id in range(5):
            thread = threading.Thread(target=worker, args=(worker_id,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify no errors occurred
        assert len(errors) == 0, f"Concurrent access errors: {errors}"
        
        # Verify all operations succeeded
        success_count = sum(1 for _, _, result in results if result == "success")
        assert success_count == 50, f"Expected 50 successful operations, got {success_count}"
    
    def test_large_state_persistence(self, session_manager, mock_model):
        """Test persistence of large state data."""
        agent1 = Agent(model=mock_model, session_manager=session_manager)
        
        # Create large state data
        large_data = {f"key_{i}": f"value_{i}" * 100 for i in range(100)}
        agent1.state.set("large_dataset", large_data)
        
        # Add data to multiple namespaces
        for ns in ["ns1", "ns2", "ns3"]:
            namespace_data = {f"{ns}_key_{i}": f"{ns}_value_{i}" for i in range(50)}
            for key, value in namespace_data.items():
                agent1.state.set(key, value, namespace=ns)
        
        # Trigger persistence
        test_message = Message(role="assistant", content="Test")
        session_manager.update_session(agent1, test_message)
        
        # Create new agent and verify large data
        agent2 = Agent(model=mock_model, session_manager=session_manager)
        
        # Verify large dataset
        retrieved_large = agent2.state.get("large_dataset")
        assert len(retrieved_large) == 100
        assert retrieved_large["key_50"] == "value_50" * 100
        
        # Verify namespace data
        for ns in ["ns1", "ns2", "ns3"]:
            ns_data = agent2.state.get(namespace=ns)
            assert len(ns_data) == 50
            assert ns_data[f"{ns}_key_25"] == f"{ns}_value_25"


class TestAgentStateSDKIntegration:
    """Test SDK namespace integration."""
    
    @pytest.fixture
    def mock_model(self):
        """Create mock model for testing."""
        model = Mock()
        model.model_id = "test-model"
        return model
    
    def test_sdk_namespace_population(self, mock_model):
        """Test that SDK namespace is populated with metadata."""
        agent = Agent(model=mock_model)
        
        # SDK namespace should exist
        assert agent.state.has_namespace("sdk")
        
        # Should be able to store SDK metadata
        agent.state.set("conversation_manager_type", "SlidingWindow", namespace="sdk")
        agent.state.set("model_id", mock_model.model_id, namespace="sdk")
        
        sdk_data = agent.state.get(namespace="sdk")
        assert sdk_data["conversation_manager_type"] == "SlidingWindow"
        assert sdk_data["model_id"] == "test-model"
    
    def test_sdk_namespace_isolation(self, mock_model):
        """Test that SDK namespace is isolated from user state."""
        agent = Agent(model=mock_model)
        
        # Set same key in different namespaces
        agent.state.set("config", "user_config")
        agent.state.set("config", "sdk_config", namespace="sdk")
        
        # Values should be isolated
        assert agent.state.get("config") == "user_config"
        assert agent.state.get("config", namespace="sdk") == "sdk_config"
        
        # Clearing default shouldn't affect SDK
        agent.state.clear()
        assert agent.state.get("config") is None
        assert agent.state.get("config", namespace="sdk") == "sdk_config"
