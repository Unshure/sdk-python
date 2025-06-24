"""Agent state management with namespaced persistence support."""

import json
from typing import Any, Dict, List, Optional


class StateValidationError(Exception):
    """Exception raised when state validation fails."""

    pass


class AgentState:
    """Manages agent state with flexible namespace support.

    Provides a namespaced key-value store for agent state with JSON serialization
    validation and persistence support. State is organized into namespaces, with
    'default' being used when no namespace is specified.

    Key features:
    - Flexible namespace management (default, custom, and reserved 'sdk')
    - JSON serialization validation on assignment
    - Get/set/clear/delete operations with namespace support
    - Automatic namespace creation on first use
    - Complete state retrieval across all namespaces
    """

    def __init__(self):
        """Initialize AgentState with default and SDK namespaces."""
        self._namespaces: Dict[str, Dict[str, Any]] = {"default": {}, "sdk": {}}

    def set(self, key: str, value: Any, namespace: str = "default") -> None:
        """Set a value in the specified namespace.

        Args:
            key: The key to store the value under
            value: The value to store (must be JSON serializable)
            namespace: The namespace to store in (defaults to "default")

        Raises:
            ValueError: If key or namespace is invalid
            StateValidationError: If value is not JSON serializable
        """
        self._validate_key(key)
        self._validate_namespace(namespace)
        self._validate_json_serializable(value)

        # Create namespace if it doesn't exist
        if namespace not in self._namespaces:
            self._namespaces[namespace] = {}

        self._namespaces[namespace][key] = value

    def get(self, key: Optional[str] = None, namespace: str = "default") -> Any:
        """Get a value or entire namespace from the specified namespace.

        Args:
            key: The key to retrieve (if None, returns entire namespace)
            namespace: The namespace to retrieve from (defaults to "default")

        Returns:
            The stored value, entire namespace dict, or None if not found

        Raises:
            ValueError: If namespace name is invalid
        """
        self._validate_namespace(namespace)

        # Return None if namespace doesn't exist
        if namespace not in self._namespaces:
            return None if key is not None else {}

        if key is None:
            # Return entire namespace
            return self._namespaces[namespace].copy()
        else:
            # Return specific key
            return self._namespaces[namespace].get(key)

    def clear(self, namespace: str = "default") -> None:
        """Clear all data in the specified namespace.

        Args:
            namespace: The namespace to clear (defaults to "default")

        Raises:
            ValueError: If namespace name is invalid
        """
        self._validate_namespace(namespace)

        # Create namespace if it doesn't exist, then clear it
        if namespace not in self._namespaces:
            self._namespaces[namespace] = {}
        else:
            self._namespaces[namespace].clear()

    def delete(self, key: str, namespace: str = "default") -> None:
        """Delete a specific key from the specified namespace.

        Args:
            key: The key to delete
            namespace: The namespace to delete from (defaults to "default")

        Raises:
            ValueError: If key or namespace is invalid
        """
        self._validate_key(key)
        self._validate_namespace(namespace)

        # Silently ignore if namespace or key doesn't exist (idempotent)
        if namespace in self._namespaces:
            self._namespaces[namespace].pop(key, None)

    def create_namespace(self, name: str) -> None:
        """Explicitly create a namespace.

        Args:
            name: The name of the namespace to create

        Raises:
            ValueError: If namespace name is invalid
        """
        self._validate_namespace(name)

        if name not in self._namespaces:
            self._namespaces[name] = {}

    def list_namespaces(self) -> List[str]:
        """List all existing namespace names.

        Returns:
            List of namespace names
        """
        return list(self._namespaces.keys())

    def has_namespace(self, name: str) -> bool:
        """Check if a namespace exists.

        Args:
            name: The namespace name to check

        Returns:
            True if namespace exists, False otherwise
        """
        return name in self._namespaces

    def to_dict(self) -> Dict[str, Dict[str, Any]]:
        """Serialize the AgentState to a dictionary.

        Returns:
            Dictionary representation of the complete state with all namespaces

        Example:
            >>> state = AgentState()
            >>> state.set("key1", "value1")
            >>> state.set("key2", "value2", namespace="custom")
            >>> state.to_dict()
            {
                "default": {"key1": "value1"},
                "custom": {"key2": "value2"},
                "sdk": {}
            }
        """
        return {namespace: data.copy() for namespace, data in self._namespaces.items()}

    @classmethod
    def from_dict(cls, data: Dict[str, Dict[str, Any]]) -> "AgentState":
        """Deserialize an AgentState from a dictionary.

        Args:
            data: Dictionary containing namespace data

        Returns:
            New AgentState instance with the provided data

        Raises:
            StateValidationError: If the data contains non-JSON-serializable values
            ValueError: If the data format is invalid

        Example:
            >>> data = {
            ...     "default": {"key1": "value1"},
            ...     "custom": {"key2": "value2"},
            ...     "sdk": {"metadata": "value"}
            ... }
            >>> state = AgentState.from_dict(data)
            >>> state.get("key1")
            'value1'
        """
        if not isinstance(data, dict):
            raise ValueError("Data must be a dictionary")

        # Create new instance
        instance = cls()

        # Clear default namespaces and populate with provided data
        instance._namespaces.clear()

        for namespace_name, namespace_data in data.items():
            if not isinstance(namespace_name, str):
                raise ValueError(f"Namespace name must be a string, got {type(namespace_name).__name__}")

            if not isinstance(namespace_data, dict):
                raise ValueError(f"Namespace data must be a dictionary, got {type(namespace_data).__name__}")

            # Validate namespace name
            instance._validate_namespace(namespace_name)

            # Create namespace and validate all values
            instance._namespaces[namespace_name] = {}
            for key, value in namespace_data.items():
                if not isinstance(key, str):
                    raise ValueError(f"Key must be a string, got {type(key).__name__}")

                # Validate key and value
                instance._validate_key(key)
                instance._validate_json_serializable(value)

                instance._namespaces[namespace_name][key] = value

        # Ensure default and SDK namespaces exist
        if "default" not in instance._namespaces:
            instance._namespaces["default"] = {}
        if "sdk" not in instance._namespaces:
            instance._namespaces["sdk"] = {}

        return instance

    def _validate_key(self, key: str) -> None:
        """Validate that a key is valid.

        Args:
            key: The key to validate

        Raises:
            ValueError: If key is invalid
        """
        if key is None:
            raise ValueError("Key cannot be None")
        if not isinstance(key, str):
            raise ValueError("Key must be a string")
        if not key.strip():
            raise ValueError("Key cannot be empty")

    def _validate_namespace(self, namespace: str) -> None:
        """Validate that a namespace name is valid.

        Args:
            namespace: The namespace name to validate

        Raises:
            ValueError: If namespace name is invalid
        """
        if namespace is None:
            raise ValueError("Namespace name cannot be None")
        if not isinstance(namespace, str):
            raise ValueError("Namespace name must be a string")
        if not namespace.strip():
            raise ValueError("Namespace name cannot be empty")

    def _validate_json_serializable(self, value: Any) -> None:
        """Validate that a value is JSON serializable.

        Args:
            value: The value to validate

        Raises:
            StateValidationError: If value is not JSON serializable
        """
        try:
            json.dumps(value)
        except (TypeError, ValueError) as e:
            raise StateValidationError(
                f"Value is not JSON serializable: {type(value).__name__}. "
                f"Only JSON-compatible types (str, int, float, bool, list, dict, None) are allowed."
            ) from e
