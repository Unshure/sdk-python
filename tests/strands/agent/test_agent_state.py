"""Tests for AgentState class."""

import json
import pytest
from unittest.mock import Mock

from strands.agent.state import AgentState, StateValidationError


class TestAgentStateBasicOperations:
    """Test basic set/get operations."""
    
    def test_set_get_default_namespace(self):
        """Test setting and getting values in default namespace."""
        state = AgentState()
        state.set("key", "value")
        assert state.get("key") == "value"
    
    def test_set_get_custom_namespace(self):
        """Test setting and getting values in custom namespace."""
        state = AgentState()
        state.set("key", "value", namespace="custom")
        assert state.get("key", namespace="custom") == "value"
    
    def test_namespace_isolation(self):
        """Test that namespaces are isolated from each other."""
        state = AgentState()
        state.set("key", "default_value")
        state.set("key", "custom_value", namespace="custom")
        
        assert state.get("key") == "default_value"
        assert state.get("key", namespace="custom") == "custom_value"
    
    def test_get_nonexistent_key_returns_none(self):
        """Test that getting nonexistent key returns None."""
        state = AgentState()
        assert state.get("nonexistent") is None
        assert state.get("nonexistent", namespace="custom") is None
    
    def test_get_entire_namespace(self):
        """Test getting entire namespace contents."""
        state = AgentState()
        state.set("key1", "value1")
        state.set("key2", "value2")
        
        result = state.get()
        expected = {"key1": "value1", "key2": "value2"}
        assert result == expected
    
    def test_get_all_namespaces(self):
        """Test getting all namespaces."""
        state = AgentState()
        state.set("default_key", "default_value")
        state.set("custom_key", "custom_value", namespace="custom")
        
        result = state.get_all()
        expected = {
            "default": {"default_key": "default_value"},
            "custom": {"custom_key": "custom_value"},
            "sdk": {}
        }
        assert result == expected


class TestAgentStateJSONValidation:
    """Test JSON serialization validation."""
    
    def test_valid_json_values(self):
        """Test that valid JSON values are accepted."""
        state = AgentState()
        
        # Test various JSON-serializable types
        state.set("string", "test")
        state.set("int", 42)
        state.set("float", 3.14)
        state.set("bool", True)
        state.set("list", [1, 2, 3])
        state.set("dict", {"nested": "value"})
        state.set("null", None)
        
        # Verify all values are stored correctly
        assert state.get("string") == "test"
        assert state.get("int") == 42
        assert state.get("float") == 3.14
        assert state.get("bool") is True
        assert state.get("list") == [1, 2, 3]
        assert state.get("dict") == {"nested": "value"}
        assert state.get("null") is None
    
    def test_invalid_json_values_raise_error(self):
        """Test that non-JSON-serializable values raise ValidationError."""
        state = AgentState()
        
        # Test various non-serializable types
        with pytest.raises(StateValidationError, match="not JSON serializable"):
            state.set("function", lambda x: x)
        
        with pytest.raises(StateValidationError, match="not JSON serializable"):
            state.set("object", object())
        
        with pytest.raises(StateValidationError, match="not JSON serializable"):
            state.set("mock", Mock())
    
    def test_complex_nested_structures(self):
        """Test complex but valid nested JSON structures."""
        state = AgentState()
        
        complex_data = {
            "users": [
                {"id": 1, "name": "Alice", "active": True},
                {"id": 2, "name": "Bob", "active": False}
            ],
            "metadata": {
                "version": "1.0",
                "settings": {
                    "debug": False,
                    "max_retries": 3
                }
            }
        }
        
        state.set("complex", complex_data)
        assert state.get("complex") == complex_data


class TestAgentStateClearOperations:
    """Test clear operations."""
    
    def test_clear_default_namespace(self):
        """Test clearing default namespace."""
        state = AgentState()
        state.set("key1", "value1")
        state.set("key2", "value2")
        
        state.clear()
        
        assert state.get() == {}
        assert state.get("key1") is None
        assert state.get("key2") is None
    
    def test_clear_custom_namespace(self):
        """Test clearing custom namespace."""
        state = AgentState()
        state.set("default_key", "default_value")
        state.set("custom_key", "custom_value", namespace="custom")
        
        state.clear(namespace="custom")
        
        # Default namespace should be unchanged
        assert state.get("default_key") == "default_value"
        # Custom namespace should be empty
        assert state.get(namespace="custom") == {}
        assert state.get("custom_key", namespace="custom") is None
    
    def test_clear_nonexistent_namespace_is_idempotent(self):
        """Test that clearing nonexistent namespace doesn't raise error."""
        state = AgentState()
        # Should not raise any exception
        state.clear(namespace="nonexistent")


class TestAgentStateDeleteOperations:
    """Test delete operations."""
    
    def test_delete_key_from_default_namespace(self):
        """Test deleting key from default namespace."""
        state = AgentState()
        state.set("key1", "value1")
        state.set("key2", "value2")
        
        state.delete("key1")
        
        assert state.get("key1") is None
        assert state.get("key2") == "value2"
    
    def test_delete_key_from_custom_namespace(self):
        """Test deleting key from custom namespace."""
        state = AgentState()
        state.set("key", "default_value")
        state.set("key", "custom_value", namespace="custom")
        
        state.delete("key", namespace="custom")
        
        # Default namespace should be unchanged
        assert state.get("key") == "default_value"
        # Key should be deleted from custom namespace
        assert state.get("key", namespace="custom") is None
    
    def test_delete_nonexistent_key_is_idempotent(self):
        """Test that deleting nonexistent key doesn't raise error."""
        state = AgentState()
        # Should not raise any exception
        state.delete("nonexistent")
        state.delete("nonexistent", namespace="custom")


class TestAgentStateNamespaceManagement:
    """Test namespace management operations."""
    
    def test_create_namespace(self):
        """Test explicit namespace creation."""
        state = AgentState()
        state.create_namespace("new_namespace")
        
        assert state.has_namespace("new_namespace")
        assert "new_namespace" in state.list_namespaces()
    
    def test_list_namespaces(self):
        """Test listing all namespaces."""
        state = AgentState()
        state.set("key", "value", namespace="custom1")
        state.set("key", "value", namespace="custom2")
        
        namespaces = state.list_namespaces()
        
        # Should include default, sdk, and custom namespaces
        assert "default" in namespaces
        assert "sdk" in namespaces
        assert "custom1" in namespaces
        assert "custom2" in namespaces
    
    def test_has_namespace(self):
        """Test checking namespace existence."""
        state = AgentState()
        
        # Default and SDK namespaces should always exist
        assert state.has_namespace("default")
        assert state.has_namespace("sdk")
        
        # Custom namespace should not exist initially
        assert not state.has_namespace("custom")
        
        # After setting value, namespace should exist
        state.set("key", "value", namespace="custom")
        assert state.has_namespace("custom")
    
    def test_automatic_namespace_creation(self):
        """Test that namespaces are created automatically on first use."""
        state = AgentState()
        
        assert not state.has_namespace("auto_created")
        
        state.set("key", "value", namespace="auto_created")
        
        assert state.has_namespace("auto_created")
        assert "auto_created" in state.list_namespaces()


class TestAgentStateSDKNamespace:
    """Test SDK namespace behavior."""
    
    def test_sdk_namespace_exists_by_default(self):
        """Test that SDK namespace exists by default."""
        state = AgentState()
        
        assert state.has_namespace("sdk")
        assert "sdk" in state.list_namespaces()
        assert state.get(namespace="sdk") == {}
    
    def test_sdk_namespace_operations(self):
        """Test operations on SDK namespace."""
        state = AgentState()
        
        state.set("metadata", "value", namespace="sdk")
        assert state.get("metadata", namespace="sdk") == "value"
        
        state.clear(namespace="sdk")
        assert state.get(namespace="sdk") == {}


class TestAgentStateErrorHandling:
    """Test error handling and edge cases."""
    
    def test_invalid_namespace_names(self):
        """Test handling of invalid namespace names."""
        state = AgentState()
        
        # Empty string should raise error
        with pytest.raises(ValueError, match="Namespace name cannot be empty"):
            state.set("key", "value", namespace="")
        
        # None should raise error
        with pytest.raises(ValueError, match="Namespace name cannot be None"):
            state.set("key", "value", namespace=None)
    
    def test_invalid_key_names(self):
        """Test handling of invalid key names."""
        state = AgentState()
        
        # Empty string should raise error
        with pytest.raises(ValueError, match="Key cannot be empty"):
            state.set("", "value")
        
        # None should raise error
        with pytest.raises(ValueError, match="Key cannot be None"):
            state.set(None, "value")
    
    def test_state_validation_error_preserves_state(self):
        """Test that validation errors don't corrupt existing state."""
        state = AgentState()
        state.set("valid_key", "valid_value")
        
        # Attempt to set invalid value
        with pytest.raises(StateValidationError):
            state.set("invalid_key", lambda x: x)
        
        # Existing state should be preserved
        assert state.get("valid_key") == "valid_value"
        assert state.get("invalid_key") is None


class TestAgentStateIntegration:
    """Test integration scenarios."""
    
    def test_state_serialization_roundtrip(self):
        """Test that state can be serialized and deserialized."""
        state = AgentState()
        state.set("key1", "value1")
        state.set("key2", {"nested": "value"})
        state.set("custom_key", "custom_value", namespace="custom")
        
        # Get all state data
        all_state = state.get_all()
        
        # Should be JSON serializable
        json_str = json.dumps(all_state)
        restored_data = json.loads(json_str)
        
        # Create new state and verify data
        new_state = AgentState()
        for namespace_name, namespace_data in restored_data.items():
            for key, value in namespace_data.items():
                new_state.set(key, value, namespace=namespace_name)
        
        assert new_state.get_all() == all_state
    
    def test_large_state_handling(self):
        """Test handling of large state data."""
        state = AgentState()
        
        # Create large but valid data structure
        large_data = {f"key_{i}": f"value_{i}" for i in range(1000)}
        state.set("large_data", large_data)
        
        # Should handle large data without issues
        retrieved = state.get("large_data")
        assert len(retrieved) == 1000
        assert retrieved["key_500"] == "value_500"
