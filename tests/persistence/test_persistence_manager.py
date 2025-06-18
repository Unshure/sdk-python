"""Tests for PersistenceManager interface."""

import pytest
from abc import ABC

from strands.persistence.persistence_manager import PersistenceManager
from strands.persistence.exceptions import PersistenceException


class TestPersistenceManager:
    """Test the PersistenceManager abstract interface."""

    def test_is_abstract_base_class(self):
        """Test that PersistenceManager is an abstract base class."""
        assert issubclass(PersistenceManager, ABC)

        # Should not be able to instantiate directly
        with pytest.raises(TypeError):
            PersistenceManager()

    def test_has_required_abstract_methods(self):
        """Test that all required abstract methods are defined."""
        expected_methods = [
            "save_agent_state",
            "save_customer_state",
            "save_request_state",
            "load_agent_state",
            "load_customer_state",
            "load_request_state",
            "delete_session",
            "session_exists",
        ]

        for method_name in expected_methods:
            assert hasattr(PersistenceManager, method_name)
            method = getattr(PersistenceManager, method_name)
            assert getattr(method, "__isabstractmethod__", False), f"{method_name} should be abstract"

    def test_concrete_implementation_must_implement_all_methods(self):
        """Test that concrete implementations must implement all abstract methods."""

        # Incomplete implementation should fail
        class IncompletePersistenceManager(PersistenceManager):
            def save_agent_state(self, session_id, agent_id, user_id, messages):
                pass

        with pytest.raises(TypeError):
            IncompletePersistenceManager()

        # Complete implementation should work
        class CompletePersistenceManager(PersistenceManager):
            def save_agent_state(self, session_id, agent_id, user_id, messages):
                pass

            def save_customer_state(self, session_id, agent_id, user_id, state):
                pass

            def save_request_state(self, session_id, agent_id, user_id, message, metrics, stop_reason):
                pass

            def load_agent_state(self, session_id, agent_id, user_id):
                return []

            def load_customer_state(self, session_id, agent_id, user_id):
                return {}

            def load_request_state(self, session_id, agent_id, user_id):
                return None

            def delete_session(self, session_id, agent_id, user_id):
                pass

            def session_exists(self, session_id, agent_id, user_id):
                return False

        # Should be able to instantiate complete implementation
        manager = CompletePersistenceManager()
        assert isinstance(manager, PersistenceManager)


class TestPersistenceException:
    """Test the PersistenceException class."""

    def test_basic_exception_creation(self):
        """Test creating a basic PersistenceException."""
        message = "Test persistence failure"
        exc = PersistenceException(message)

        assert str(exc) == message
        assert exc.cause is None

    def test_exception_with_cause(self):
        """Test creating PersistenceException with underlying cause."""
        message = "Persistence operation failed"
        cause = ValueError("Invalid data format")
        exc = PersistenceException(message, cause)

        assert exc.cause == cause
        assert message in str(exc)
        assert "Invalid data format" in str(exc)

    def test_exception_inheritance(self):
        """Test that PersistenceException inherits from Exception."""
        exc = PersistenceException("test")
        assert isinstance(exc, Exception)

        # Should be catchable as Exception
        try:
            raise exc
        except Exception as caught:
            assert isinstance(caught, PersistenceException)
