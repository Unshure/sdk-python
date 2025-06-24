"""Session manager interface for agent session management."""

from abc import ABC, abstractmethod
from typing import List, Optional

from .models import Session, SessionSummary, SessionFilter


class SessionDatastore(ABC):
    @abstractmethod
    def create_session(self, session: Session) -> str:
        """Create a new session.

        Args:
            session: Session object to create

        Returns:
            Session identifier for the created session

        Raises:
            SessionException: If session creation fails
        """
        raise NotImplementedError("Subclasses must implement create_session")

    @abstractmethod
    def read_session(self, session_id: str) -> Session:
        """Read current session data.

        Returns:
            Session object containing all session data

        Raises:
            SessionException: If session doesn't exist or read fails
        """
        raise NotImplementedError("Subclasses must implement read_session")

    @abstractmethod
    def update_session(self, session: Session) -> None:
        """Update current session data.

        Args:
            session: Updated session object to save

        Raises:
            SessionException: If session doesn't exist or update fails
        """
        raise NotImplementedError("Subclasses must implement update_session")

    @abstractmethod
    def delete_session(self, session_id: str) -> None:
        """Delete the current session.

        Removes all data associated with the current session.

        Raises:
            SessionException: If session doesn't exist or delete fails
        """
        raise NotImplementedError("Subclasses must implement delete_session")

    @abstractmethod
    def list_sessions(self, session_filter: Optional[SessionFilter] = None) -> List[SessionSummary]:
        """List available sessions with optional filtering.

        Args:
            session_filter: Optional filter criteria for sessions

        Returns:
            List of session summaries that match the filter criteria

        Raises:
            SessionException: If list operation fails
        """
        raise NotImplementedError("Subclasses must implement list_sessions")
