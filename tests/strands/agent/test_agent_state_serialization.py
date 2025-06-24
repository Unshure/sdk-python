"""Tests for AgentState dictionary serialization and deserialization."""

import pytest
from strands.agent.state import AgentState, StateValidationError


class TestAgentStateDictSerialization:
    """Test AgentState dictionary serialization methods."""

    def test_to_dict_empty_state(self):
        """Test serializing empty state to dictionary."""
        state = AgentState()
        result = state.to_dict()

        expected = {"default": {}, "sdk": {}}
        assert result == expected

    def test_to_dict_with_data(self):
        """Test serializing state with data to dictionary."""
        state = AgentState()
        state.set("key1", "value1")
        state.set("key2", 42)
        state.set("custom_key", "custom_value", namespace="custom")
        state.set("sdk_key", "sdk_value", namespace="sdk")

        result = state.to_dict()

        expected = {
            "default": {"key1": "value1", "key2": 42},
            "custom": {"custom_key": "custom_value"},
            "sdk": {"sdk_key": "sdk_value"},
        }
        assert result == expected

    def test_to_dict_returns_copy(self):
        """Test that to_dict returns a copy, not reference."""
        state = AgentState()
        state.set("key", "value")

        result = state.to_dict()

        # Modify the returned dict
        result["default"]["key"] = "modified"

        # Original state should be unchanged
        assert state.get("key") == "value"

    def test_to_dict_complex_data(self):
        """Test serializing complex but valid JSON data."""
        state = AgentState()
        complex_data = {"nested": {"key": "value"}, "list": [1, 2, 3], "mixed": [{"a": 1}, {"b": 2}]}
        state.set("complex", complex_data)

        result = state.to_dict()

        assert result["default"]["complex"] == complex_data

    def test_from_dict_empty_data(self):
        """Test deserializing empty dictionary."""
        data = {"default": {}, "sdk": {}}
        state = AgentState.from_dict(data)

        assert state.to_dict() == {"default": {}, "sdk": {}}

    def test_from_dict_with_data(self):
        """Test deserializing dictionary with data."""
        data = {
            "default": {"key1": "value1", "key2": 42},
            "custom": {"custom_key": "custom_value"},
            "sdk": {"sdk_key": "sdk_value"},
        }

        state = AgentState.from_dict(data)

        assert state.get("key1") == "value1"
        assert state.get("key2") == 42
        assert state.get("custom_key", namespace="custom") == "custom_value"
        assert state.get("sdk_key", namespace="sdk") == "sdk_value"

    def test_from_dict_missing_default_namespace(self):
        """Test that missing default namespace is created."""
        data = {"custom": {"key": "value"}}
        state = AgentState.from_dict(data)

        assert state.has_namespace("default")
        assert state.has_namespace("sdk")
        assert state.get(namespace="default") == {}

    def test_from_dict_missing_sdk_namespace(self):
        """Test that missing SDK namespace is created."""
        data = {"default": {"key": "value"}}
        state = AgentState.from_dict(data)

        assert state.has_namespace("sdk")
        assert state.get(namespace="sdk") == {}

    def test_from_dict_invalid_data_type(self):
        """Test from_dict with invalid data type."""
        with pytest.raises(ValueError, match="Data must be a dictionary"):
            AgentState.from_dict("not a dict")

    def test_from_dict_invalid_namespace_name(self):
        """Test from_dict with invalid namespace name."""
        data = {123: {"key": "value"}}
        with pytest.raises(ValueError, match="Namespace name must be a string"):
            AgentState.from_dict(data)

    def test_from_dict_invalid_namespace_data(self):
        """Test from_dict with invalid namespace data."""
        data = {"default": "not a dict"}
        with pytest.raises(ValueError, match="Namespace data must be a dictionary"):
            AgentState.from_dict(data)

    def test_from_dict_invalid_key_type(self):
        """Test from_dict with invalid key type."""
        data = {"default": {123: "value"}}
        with pytest.raises(ValueError, match="Key must be a string"):
            AgentState.from_dict(data)

    def test_from_dict_invalid_namespace_name_validation(self):
        """Test from_dict with invalid namespace name that fails validation."""
        data = {"": {"key": "value"}}
        with pytest.raises(ValueError, match="Namespace name cannot be empty"):
            AgentState.from_dict(data)

    def test_from_dict_invalid_key_validation(self):
        """Test from_dict with invalid key that fails validation."""
        data = {"default": {"": "value"}}
        with pytest.raises(ValueError, match="Key cannot be empty"):
            AgentState.from_dict(data)

    def test_dict_serialization_roundtrip(self):
        """Test complete dictionary serialization and deserialization roundtrip."""
        # Create original state
        original = AgentState()
        original.set("string", "test")
        original.set("number", 42)
        original.set("float", 3.14)
        original.set("boolean", True)
        original.set("null", None)
        original.set("list", [1, 2, 3])
        original.set("dict", {"nested": "value"})
        original.set("custom_key", "custom_value", namespace="custom")
        original.set("sdk_key", "sdk_value", namespace="sdk")

        # Serialize to dict
        data = original.to_dict()

        # Deserialize from dict
        restored = AgentState.from_dict(data)

        # Verify all data is preserved
        assert restored.to_dict() == original.to_dict()
        assert restored.get("string") == "test"
        assert restored.get("number") == 42
        assert restored.get("float") == 3.14
        assert restored.get("boolean") is True
        assert restored.get("null") is None
        assert restored.get("list") == [1, 2, 3]
        assert restored.get("dict") == {"nested": "value"}
        assert restored.get("custom_key", namespace="custom") == "custom_value"
        assert restored.get("sdk_key", namespace="sdk") == "sdk_value"


class TestAgentStateSerializationIntegration:
    """Test integration scenarios for AgentState dictionary serialization."""

    def test_serialization_preserves_namespace_structure(self):
        """Test that serialization preserves namespace structure."""
        state = AgentState()

        # Create multiple namespaces with various data
        state.create_namespace("user_settings")
        state.create_namespace("app_config")

        state.set("default_key", "default_value")
        state.set("user_pref", "dark_mode", namespace="user_settings")
        state.set("theme", "blue", namespace="user_settings")
        state.set("debug", True, namespace="app_config")
        state.set("version", "1.0.0", namespace="app_config")
        state.set("metadata", {"type": "agent"}, namespace="sdk")

        # Serialize and deserialize
        data = state.to_dict()
        restored = AgentState.from_dict(data)

        # Verify namespace structure is preserved
        assert set(restored.list_namespaces()) == {"default", "user_settings", "app_config", "sdk"}

        # Verify all data is preserved
        assert restored.get("default_key") == "default_value"
        assert restored.get("user_pref", namespace="user_settings") == "dark_mode"
        assert restored.get("theme", namespace="user_settings") == "blue"
        assert restored.get("debug", namespace="app_config") is True
        assert restored.get("version", namespace="app_config") == "1.0.0"
        assert restored.get("metadata", namespace="sdk") == {"type": "agent"}

    def test_serialization_with_large_data(self):
        """Test serialization with large amounts of data."""
        state = AgentState()

        # Create large dataset
        large_data = {f"key_{i}": f"value_{i}" for i in range(1000)}
        state.set("large_dataset", large_data)

        # Add data to multiple namespaces
        for i in range(10):
            namespace = f"namespace_{i}"
            for j in range(100):
                state.set(f"key_{j}", f"value_{j}", namespace=namespace)

        # Serialize and deserialize
        data = state.to_dict()
        restored = AgentState.from_dict(data)

        # Verify large dataset
        assert restored.get("large_dataset") == large_data

        # Verify namespace data
        for i in range(10):
            namespace = f"namespace_{i}"
            for j in range(100):
                assert restored.get(f"key_{j}", namespace=namespace) == f"value_{j}"

    def test_serialization_compatibility_with_session_storage(self):
        """Test that serialized state is compatible with session storage format."""
        state = AgentState()
        state.set("session_data", "test_value")
        state.set("user_id", "user123", namespace="sdk")

        # Serialize to dict (as used by session storage)
        state_dict = state.to_dict()

        # This should be compatible with session.state field
        from strands.session.models import Session

        session = Session(session_id="test", user_id="user", agent_id="agent", state=state_dict)

        # Verify session serialization works
        session_dict = session.to_dict()
        assert "state" in session_dict
        assert session_dict["state"] == state_dict

        # Verify session deserialization works
        restored_session = Session.from_dict(session_dict)
        restored_state = AgentState.from_dict(restored_session.state)

        assert restored_state.get("session_data") == "test_value"
        assert restored_state.get("user_id", namespace="sdk") == "user123"

    def test_serialization_with_unicode_data(self):
        """Test serialization with Unicode characters."""
        state = AgentState()
        state.set("unicode", "Hello 世界 🌍")
        state.set("emoji", "🚀✨🎉")

        data = state.to_dict()
        restored = AgentState.from_dict(data)

        assert restored.get("unicode") == "Hello 世界 🌍"
        assert restored.get("emoji") == "🚀✨🎉"

    def test_deserialization_validation(self):
        """Test that deserialization validates all data."""
        # Test with empty namespace name
        data = {"": {"key": "value"}}
        with pytest.raises(ValueError, match="Namespace name cannot be empty"):
            AgentState.from_dict(data)

        # Test with empty key name
        data = {"default": {"": "value"}}
        with pytest.raises(ValueError, match="Key cannot be empty"):
            AgentState.from_dict(data)

    def test_serialization_data_types_preservation(self):
        """Test that all JSON-compatible data types are preserved through serialization."""
        state = AgentState()

        # Test all JSON-compatible types
        test_data = {
            "string": "test_string",
            "integer": 42,
            "float": 3.14159,
            "boolean_true": True,
            "boolean_false": False,
            "null_value": None,
            "empty_list": [],
            "list_with_data": [1, "two", 3.0, True, None],
            "empty_dict": {},
            "nested_dict": {"level1": {"level2": {"deep_value": "found"}}},
            "mixed_structure": {
                "users": [{"id": 1, "name": "Alice", "active": True}, {"id": 2, "name": "Bob", "active": False}],
                "metadata": {"version": "1.0", "settings": {"debug": False, "max_retries": 3}},
            },
        }

        # Set all test data
        for key, value in test_data.items():
            state.set(key, value)

        # Serialize and deserialize
        data = state.to_dict()
        restored = AgentState.from_dict(data)

        # Verify all data types are preserved
        for key, expected_value in test_data.items():
            actual_value = restored.get(key)
            assert actual_value == expected_value
            assert type(actual_value) == type(expected_value)
