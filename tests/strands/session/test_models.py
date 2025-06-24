"""Tests for session models with state support."""

import pytest
from datetime import datetime
from strands.session.models import Session


class TestSessionWithState:
    """Test Session model with state field."""
    
    def test_session_creation_with_empty_state(self):
        """Test that new sessions have empty state by default."""
        session = Session.create_new("user123", "agent456")
        
        assert hasattr(session, 'state')
        assert session.state == {}
    
    def test_session_creation_with_initial_state(self):
        """Test creating session with initial state data."""
        initial_state = {
            "default": {"key": "value"},
            "custom": {"setting": "enabled"}
        }
        
        session = Session(
            session_id="test_session",
            user_id="user123",
            agent_id="agent456",
            state=initial_state
        )
        
        assert session.state == initial_state
    
    def test_session_to_dict_includes_state(self):
        """Test that to_dict() includes state field."""
        session = Session.create_new("user123", "agent456")
        session.state = {
            "default": {"tool_count": 5},
            "sdk": {"conversation_type": "sliding"}
        }
        
        session_dict = session.to_dict()
        
        assert "state" in session_dict
        assert session_dict["state"] == session.state
    
    def test_session_from_dict_with_state(self):
        """Test creating session from dict with state field."""
        session_data = {
            "session_id": "test_session",
            "user_id": "user123",
            "agent_id": "agent456",
            "messages": [],
            "state": {
                "default": {"key": "value"},
                "custom": {"setting": True}
            },
            "created_at": "2024-06-24T12:00:00Z",
            "updated_at": "2024-06-24T12:00:00Z"
        }
        
        session = Session.from_dict(session_data)
        
        assert session.state == session_data["state"]
        assert session.session_id == "test_session"
        assert session.user_id == "user123"
        assert session.agent_id == "agent456"
    
    def test_session_from_dict_without_state_field(self):
        """Test backward compatibility - session dict without state field."""
        session_data = {
            "session_id": "test_session",
            "user_id": "user123",
            "agent_id": "agent456",
            "messages": [],
            "created_at": "2024-06-24T12:00:00Z",
            "updated_at": "2024-06-24T12:00:00Z"
        }
        
        session = Session.from_dict(session_data)
        
        # Should default to empty state
        assert session.state == {}
        assert session.session_id == "test_session"
    
    def test_session_serialization_roundtrip_with_state(self):
        """Test complete serialization roundtrip with state data."""
        original_session = Session.create_new("user123", "agent456")
        original_session.state = {
            "default": {
                "tool_executions": 10,
                "api_key": "secret123"
            },
            "user_settings": {
                "theme": "dark",
                "notifications": True
            },
            "sdk": {
                "conversation_manager": "SlidingWindow",
                "last_summary": "User discussed project requirements"
            }
        }
        original_session.add_message({"role": "user", "content": "Hello"})
        
        # Serialize to dict
        session_dict = original_session.to_dict()
        
        # Deserialize back to session
        restored_session = Session.from_dict(session_dict)
        
        # Verify all data is preserved
        assert restored_session.state == original_session.state
        assert restored_session.session_id == original_session.session_id
        assert restored_session.user_id == original_session.user_id
        assert restored_session.agent_id == original_session.agent_id
        assert restored_session.messages == original_session.messages
    
    def test_session_state_modification(self):
        """Test modifying session state after creation."""
        session = Session.create_new("user123", "agent456")
        
        # Initially empty
        assert session.state == {}
        
        # Modify state
        session.state["default"] = {"key": "value"}
        session.state["custom"] = {"setting": "enabled"}
        
        # Verify modifications
        assert session.state["default"]["key"] == "value"
        assert session.state["custom"]["setting"] == "enabled"
    
    def test_session_state_with_complex_data(self):
        """Test session state with complex nested data structures."""
        complex_state = {
            "default": {
                "counters": {
                    "tool_calls": 15,
                    "errors": 2,
                    "retries": 1
                },
                "configuration": {
                    "max_tokens": 1000,
                    "temperature": 0.7,
                    "model_settings": {
                        "streaming": True,
                        "timeout": 30
                    }
                }
            },
            "user_profile": {
                "preferences": {
                    "language": "en",
                    "timezone": "UTC",
                    "features": ["advanced_mode", "debug_logs"]
                }
            },
            "sdk": {
                "conversation_metadata": {
                    "total_messages": 25,
                    "last_summary_at": 20,
                    "summary_count": 2
                }
            }
        }
        
        session = Session.create_new("user123", "agent456")
        session.state = complex_state
        
        # Test serialization roundtrip with complex data
        session_dict = session.to_dict()
        restored_session = Session.from_dict(session_dict)
        
        assert restored_session.state == complex_state
    
    def test_session_state_empty_namespaces(self):
        """Test handling of empty namespaces in state."""
        session = Session.create_new("user123", "agent456")
        session.state = {
            "default": {},
            "empty_namespace": {},
            "populated": {"key": "value"}
        }
        
        session_dict = session.to_dict()
        restored_session = Session.from_dict(session_dict)
        
        assert restored_session.state["default"] == {}
        assert restored_session.state["empty_namespace"] == {}
        assert restored_session.state["populated"] == {"key": "value"}


class TestSessionBackwardCompatibility:
    """Test backward compatibility with existing sessions."""
    
    def test_existing_session_dict_format(self):
        """Test that existing session dict format still works."""
        # This represents how sessions were stored before state field
        old_session_data = {
            "session_id": "old_session",
            "user_id": "user123",
            "agent_id": "agent456",
            "messages": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"}
            ],
            "created_at": "2024-06-20T10:00:00Z",
            "updated_at": "2024-06-20T10:05:00Z"
        }
        
        # Should load without errors
        session = Session.from_dict(old_session_data)
        
        assert session.session_id == "old_session"
        assert session.state == {}  # Should default to empty state
        assert len(session.messages) == 2
    
    def test_mixed_session_data_formats(self):
        """Test handling mixed old and new session formats."""
        # Old format session
        old_session = Session.from_dict({
            "session_id": "old",
            "user_id": "user1",
            "agent_id": "agent1",
            "messages": []
        })
        
        # New format session
        new_session = Session.from_dict({
            "session_id": "new",
            "user_id": "user2", 
            "agent_id": "agent2",
            "messages": [],
            "state": {"default": {"key": "value"}}
        })
        
        assert old_session.state == {}
        assert new_session.state == {"default": {"key": "value"}}
        
        # Both should serialize correctly
        old_dict = old_session.to_dict()
        new_dict = new_session.to_dict()
        
        assert "state" in old_dict
        assert "state" in new_dict
        assert old_dict["state"] == {}
        assert new_dict["state"] == {"default": {"key": "value"}}


class TestSessionStateEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_session_with_none_state(self):
        """Test handling of None state value."""
        session = Session(
            session_id="test",
            user_id="user",
            agent_id="agent",
            state=None
        )
        
        # Should handle None gracefully
        session_dict = session.to_dict()
        assert session_dict["state"] is None
        
        # Restoration should handle None
        restored = Session.from_dict(session_dict)
        assert restored.state is None
    
    def test_session_state_type_preservation(self):
        """Test that state data types are preserved through serialization."""
        state_data = {
            "default": {
                "string": "text",
                "integer": 42,
                "float": 3.14,
                "boolean": True,
                "null": None,
                "list": [1, 2, 3],
                "nested_dict": {"inner": "value"}
            }
        }
        
        session = Session.create_new("user", "agent")
        session.state = state_data
        
        # Serialize and deserialize
        session_dict = session.to_dict()
        restored = Session.from_dict(session_dict)
        
        # Verify all types are preserved
        default_ns = restored.state["default"]
        assert isinstance(default_ns["string"], str)
        assert isinstance(default_ns["integer"], int)
        assert isinstance(default_ns["float"], float)
        assert isinstance(default_ns["boolean"], bool)
        assert default_ns["null"] is None
        assert isinstance(default_ns["list"], list)
        assert isinstance(default_ns["nested_dict"], dict)
