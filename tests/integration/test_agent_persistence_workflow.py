"""Integration tests for end-to-end agent persistence workflow."""

import json
import os
import tempfile
import shutil
from unittest.mock import Mock, patch
import pytest

from strands.agent.agent import Agent
from strands.persistence.file_persistence_manager import FilePersistenceManager
from strands.persistence.exceptions import PersistenceException
from strands.telemetry.metrics import EventLoopMetrics


class TestAgentPersistenceWorkflow:
    """Integration tests for complete agent persistence workflow."""

    @pytest.fixture
    def temp_storage_dir(self):
        """Create a temporary storage directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def persistence_manager(self, temp_storage_dir):
        """Create a FilePersistenceManager for testing."""
        return FilePersistenceManager(storage_dir=temp_storage_dir)

    def test_complete_agent_lifecycle_with_persistence(self, persistence_manager, temp_storage_dir):
        """Test complete agent lifecycle: create, interact, persist, restart, restore."""
        session_id = "test_session_123"
        agent_id = "test_agent"
        user_id = "test_user_456"

        # Phase 1: Create agent and simulate interaction
        agent1 = Agent(
            persistence_manager=persistence_manager, session_id=session_id, agent_id=agent_id, user_id=user_id
        )

        # Simulate adding messages to conversation
        messages = [
            {"role": "user", "content": [{"text": "Hello, how are you?"}]},
            {"role": "assistant", "content": [{"text": "I'm doing well, thank you for asking!"}]},
            {"role": "user", "content": [{"text": "What's the weather like?"}]},
        ]
        agent1.messages.extend(messages)

        # Update customer state
        customer_state = {
            "preference": "friendly",
            "language": "en",
            "timezone": "UTC",
            "settings": {"notifications": True, "theme": "light"},
        }
        agent1.update_customer_state(customer_state)

        # Force save the conversation state
        agent1._persistence_callback.force_save_agent_state(agent1.messages)

        # Simulate request state
        metrics = EventLoopMetrics(cycle_count=2, cycle_durations=[1.2, 0.8])
        latest_message = {"role": "assistant", "content": [{"text": "Latest response"}]}
        stop_reason = "end_turn"
        agent1._persistence_callback.force_save_request_state(latest_message, metrics, stop_reason)

        # Verify files were created
        session_dir = os.path.join(temp_storage_dir, f"{session_id}_{agent_id}_{user_id}")
        assert os.path.exists(session_dir)
        assert os.path.exists(os.path.join(session_dir, "agent_state.json"))
        assert os.path.exists(os.path.join(session_dir, "customer_state.json"))
        assert os.path.exists(os.path.join(session_dir, "request_state.json"))

        # Phase 2: Create new agent instance (simulating restart)
        agent2 = Agent(
            persistence_manager=persistence_manager, session_id=session_id, agent_id=agent_id, user_id=user_id
        )

        # Verify state was automatically restored
        assert agent2.messages == messages
        assert agent2.customer_state == customer_state

        # Verify request state can be manually restored
        restored_request_state = agent2.restore_request_state()
        assert restored_request_state is not None
        assert restored_request_state["message"] == latest_message
        assert restored_request_state["stop_reason"] == stop_reason
        assert restored_request_state["metrics"]["cycle_count"] == 2

        # Phase 3: Continue interaction with restored agent
        new_message = {"role": "assistant", "content": [{"text": "Continuing conversation"}]}
        agent2.messages.append(new_message)

        # Update customer state
        agent2.update_customer_state({"last_interaction": "2023-12-01"})

        # Force save the updated state
        agent2._persistence_callback.force_save_agent_state(agent2.messages)

        # Phase 4: Verify persistence of continued interaction
        agent3 = Agent(
            persistence_manager=persistence_manager, session_id=session_id, agent_id=agent_id, user_id=user_id
        )

        expected_messages = messages + [new_message]
        expected_customer_state = customer_state.copy()
        expected_customer_state["last_interaction"] = "2023-12-01"

        assert agent3.messages == expected_messages
        assert agent3.customer_state == expected_customer_state

    def test_multiple_sessions_isolation(self, persistence_manager):
        """Test that multiple sessions are properly isolated."""
        # Create two different sessions
        session1_data = {
            "session_id": "session_1",
            "agent_id": "agent_1",
            "user_id": "user_1",
            "messages": [{"role": "user", "content": [{"text": "Session 1 message"}]}],
            "customer_state": {"preference": "session1"},
        }

        session2_data = {
            "session_id": "session_2",
            "agent_id": "agent_2",
            "user_id": "user_2",
            "messages": [{"role": "user", "content": [{"text": "Session 2 message"}]}],
            "customer_state": {"preference": "session2"},
        }

        # Create agents for both sessions
        agent1 = Agent(
            persistence_manager=persistence_manager,
            session_id=session1_data["session_id"],
            agent_id=session1_data["agent_id"],
            user_id=session1_data["user_id"],
        )

        agent2 = Agent(
            persistence_manager=persistence_manager,
            session_id=session2_data["session_id"],
            agent_id=session2_data["agent_id"],
            user_id=session2_data["user_id"],
        )

        # Set different state for each session
        agent1.messages = session1_data["messages"]
        agent1.update_customer_state(session1_data["customer_state"])

        agent2.messages = session2_data["messages"]
        agent2.update_customer_state(session2_data["customer_state"])

        # Force save both sessions
        agent1._persistence_callback.force_save_agent_state(agent1.messages)
        agent2._persistence_callback.force_save_agent_state(agent2.messages)

        # Create new agent instances and verify isolation
        restored_agent1 = Agent(
            persistence_manager=persistence_manager,
            session_id=session1_data["session_id"],
            agent_id=session1_data["agent_id"],
            user_id=session1_data["user_id"],
        )

        restored_agent2 = Agent(
            persistence_manager=persistence_manager,
            session_id=session2_data["session_id"],
            agent_id=session2_data["agent_id"],
            user_id=session2_data["user_id"],
        )

        # Verify each session has its own data
        assert restored_agent1.messages == session1_data["messages"]
        assert restored_agent1.customer_state == session1_data["customer_state"]

        assert restored_agent2.messages == session2_data["messages"]
        assert restored_agent2.customer_state == session2_data["customer_state"]

        # Verify they don't interfere with each other
        assert restored_agent1.messages != restored_agent2.messages
        assert restored_agent1.customer_state != restored_agent2.customer_state

    def test_session_clearing_workflow(self, persistence_manager, temp_storage_dir):
        """Test complete session clearing workflow."""
        session_id = "clear_test_session"
        agent_id = "clear_test_agent"
        user_id = "clear_test_user"

        # Create agent with data
        agent = Agent(
            persistence_manager=persistence_manager, session_id=session_id, agent_id=agent_id, user_id=user_id
        )

        # Add data
        agent.messages = [{"role": "user", "content": [{"text": "Test message"}]}]
        agent.update_customer_state({"key": "value"})

        # Force save
        agent._persistence_callback.force_save_agent_state(agent.messages)

        # Verify files exist
        session_dir = os.path.join(temp_storage_dir, f"{session_id}_{agent_id}_{user_id}")
        assert os.path.exists(session_dir)

        # Clear session
        agent.clear_session()

        # Verify files are deleted
        assert not os.path.exists(session_dir)

        # Verify in-memory state is cleared
        assert agent.messages == []
        assert agent.customer_state == {}

        # Create new agent - should not restore any data
        new_agent = Agent(
            persistence_manager=persistence_manager, session_id=session_id, agent_id=agent_id, user_id=user_id
        )

        assert new_agent.messages == []
        assert new_agent.customer_state == {}

    def test_persistence_with_large_data_sets(self, persistence_manager):
        """Test persistence with large conversation histories and complex customer state."""
        session_id = "large_data_session"
        agent_id = "large_data_agent"
        user_id = "large_data_user"

        # Create agent
        agent = Agent(
            persistence_manager=persistence_manager, session_id=session_id, agent_id=agent_id, user_id=user_id
        )

        # Create large message history (100 messages)
        large_messages = []
        for i in range(100):
            role = "user" if i % 2 == 0 else "assistant"
            large_messages.append(
                {
                    "role": role,
                    "content": [{"text": f"Message {i}: " + "x" * 100}],  # Long messages
                }
            )

        agent.messages = large_messages

        # Create complex customer state
        complex_customer_state = {
            "user_profile": {
                "name": "Test User",
                "preferences": {
                    "communication_style": "detailed",
                    "topics_of_interest": ["technology", "science", "history"],
                    "language_settings": {"primary": "en", "secondary": ["es", "fr"], "formality": "casual"},
                },
                "interaction_history": {
                    "total_sessions": 50,
                    "favorite_features": ["search", "analysis", "summarization"],
                    "feedback_scores": [4.5, 4.8, 4.2, 4.9, 4.6],
                },
            },
            "session_metadata": {
                "start_time": "2023-12-01T10:00:00Z",
                "device_info": {"platform": "web", "browser": "chrome", "version": "119.0"},
                "feature_flags": {"advanced_mode": True, "beta_features": False, "analytics": True},
            },
        }

        agent.update_customer_state(complex_customer_state)

        # Force save
        agent._persistence_callback.force_save_agent_state(agent.messages)

        # Create new agent and verify restoration
        restored_agent = Agent(
            persistence_manager=persistence_manager, session_id=session_id, agent_id=agent_id, user_id=user_id
        )

        # Verify large data was properly persisted and restored
        assert len(restored_agent.messages) == 100
        assert restored_agent.messages == large_messages
        assert restored_agent.customer_state == complex_customer_state

        # Verify specific nested data
        assert restored_agent.customer_state["user_profile"]["preferences"]["language_settings"]["primary"] == "en"
        assert len(restored_agent.customer_state["user_profile"]["interaction_history"]["feedback_scores"]) == 5

    def test_error_recovery_scenarios(self, temp_storage_dir):
        """Test error recovery scenarios with corrupted or missing data."""
        persistence_manager = FilePersistenceManager(storage_dir=temp_storage_dir)
        session_id = "error_test_session"
        agent_id = "error_test_agent"
        user_id = "error_test_user"

        # Create session directory manually
        session_dir = os.path.join(temp_storage_dir, f"{session_id}_{agent_id}_{user_id}")
        os.makedirs(session_dir, exist_ok=True)

        # Test 1: Corrupted JSON file
        corrupted_file = os.path.join(session_dir, "agent_state.json")
        with open(corrupted_file, "w") as f:
            f.write("invalid json {")

        with pytest.raises(PersistenceException):
            Agent(persistence_manager=persistence_manager, session_id=session_id, agent_id=agent_id, user_id=user_id)

        # Clean up corrupted file
        os.remove(corrupted_file)

        # Test 2: Missing required fields in request state
        invalid_request_state = {"message": "incomplete"}
        request_state_file = os.path.join(session_dir, "request_state.json")
        with open(request_state_file, "w") as f:
            json.dump(invalid_request_state, f)

        # Create valid agent state and customer state files
        agent_state_file = os.path.join(session_dir, "agent_state.json")
        with open(agent_state_file, "w") as f:
            json.dump([], f)

        customer_state_file = os.path.join(session_dir, "customer_state.json")
        with open(customer_state_file, "w") as f:
            json.dump({}, f)

        # Agent should initialize successfully (request state is optional)
        agent = Agent(
            persistence_manager=persistence_manager, session_id=session_id, agent_id=agent_id, user_id=user_id
        )

        # But request state restoration should fail
        with pytest.raises(PersistenceException):
            agent.restore_request_state()

    def test_performance_with_frequent_updates(self, persistence_manager):
        """Test performance characteristics with frequent state updates."""
        session_id = "perf_test_session"
        agent_id = "perf_test_agent"
        user_id = "perf_test_user"

        agent = Agent(
            persistence_manager=persistence_manager, session_id=session_id, agent_id=agent_id, user_id=user_id
        )

        # Simulate frequent customer state updates
        import time

        start_time = time.time()

        for i in range(50):  # 50 updates
            agent.update_customer_state({f"update_{i}": f"value_{i}", "timestamp": time.time(), "counter": i})

        end_time = time.time()
        duration = end_time - start_time

        # Should complete reasonably quickly (less than 5 seconds for 50 updates)
        assert duration < 5.0, f"Performance test took too long: {duration} seconds"

        # Verify final state
        assert agent.customer_state["counter"] == 49
        assert "update_49" in agent.customer_state

        # Verify persistence worked
        restored_agent = Agent(
            persistence_manager=persistence_manager, session_id=session_id, agent_id=agent_id, user_id=user_id
        )

        assert restored_agent.customer_state["counter"] == 49
        assert "update_49" in restored_agent.customer_state

    def test_backward_compatibility_with_existing_conversation_manager(self, persistence_manager):
        """Test that persistence works alongside existing ConversationManager."""
        from strands.agent.conversation_manager import SlidingWindowConversationManager

        # Create agent with both persistence and conversation manager
        conversation_manager = SlidingWindowConversationManager()

        agent = Agent(
            persistence_manager=persistence_manager,
            conversation_manager=conversation_manager,
            session_id="compat_session",
            agent_id="compat_agent",
            user_id="compat_user",
        )

        # Verify both managers are present
        assert agent.persistence_manager == persistence_manager
        assert agent.conversation_manager == conversation_manager

        # Add messages and update customer state
        messages = [{"role": "user", "content": [{"text": f"Message {i}"}]} for i in range(5)]
        agent.messages.extend(messages)
        agent.update_customer_state({"test": "compatibility"})

        # Force save
        agent._persistence_callback.force_save_agent_state(agent.messages)

        # Create new agent and verify restoration works with conversation manager
        restored_agent = Agent(
            persistence_manager=persistence_manager,
            conversation_manager=SlidingWindowConversationManager(),
            session_id="compat_session",
            agent_id="compat_agent",
            user_id="compat_user",
        )

        assert restored_agent.messages == messages
        assert restored_agent.customer_state == {"test": "compatibility"}
        assert isinstance(restored_agent.conversation_manager, SlidingWindowConversationManager)
