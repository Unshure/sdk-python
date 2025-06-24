"""Data models for session management."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4



@dataclass
class Session:
    """Model representing an agent session.
    
    A session contains all the data associated with an agent interaction,
    including conversation history, user information, and agent state.
    """
    session_id: str
    user_id: str
    agent_id: str
    messages: List[Any] = field(default_factory=list)
    state: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Set timestamps if not provided."""
        now = datetime.utcnow()
        if self.created_at is None:
            self.created_at = now
        if self.updated_at is None:
            self.updated_at = now
    
    @classmethod
    def create_new(cls, user_id: str, agent_id: str, **kwargs) -> 'Session':
        """Create a new session with auto-generated session_id.
        
        Args:
            user_id: Unique user identifier
            agent_id: Unique agent identifier
            **kwargs: Additional session data
            
        Returns:
            New Session instance
        """
        return cls(
            session_id=str(uuid4()),
            user_id=user_id,
            agent_id=agent_id,
            **kwargs
        )
    
    def add_message(self, message: Any) -> None:
        """Add a message to the session.
        
        Args:
            message: Message to add to the conversation
        """
        self.messages.append(message)
        self.updated_at = datetime.utcnow()

    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary for serialization.
        
        Returns:
            Dictionary representation of the session
        """
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "agent_id": self.agent_id,
            "messages": self.messages,
            "state": self.state,
            "created_at": self.created_at.isoformat() + "Z" if self.created_at else None,
            "updated_at": self.updated_at.isoformat() + "Z" if self.updated_at else None,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Session':
        """Create session from dictionary.
        
        Args:
            data: Dictionary containing session data
            
        Returns:
            Session instance
        """
        # Parse timestamps
        created_at = None
        if data.get("created_at"):
            created_at = datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
        
        updated_at = None
        if data.get("updated_at"):
            updated_at = datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00"))
        
        return cls(
            session_id=data["session_id"],
            user_id=data["user_id"],
            agent_id=data["agent_id"],
            messages=data.get("messages", []),
            state=data.get("state", {}),
            created_at=created_at,
            updated_at=updated_at,
        )


@dataclass
class SessionSummary:
    """Summary model for listing sessions without full message history.
    
    This is useful for listing sessions without loading all the message data.
    """
    session_id: str
    user_id: str
    agent_id: str
    message_count: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session summary to dictionary.
        
        Returns:
            Dictionary representation of the session summary
        """
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "agent_id": self.agent_id,
            "message_count": self.message_count,
            "created_at": self.created_at.isoformat() + "Z" if self.created_at else None,
            "updated_at": self.updated_at.isoformat() + "Z" if self.updated_at else None,
        }
    
    @classmethod
    def from_session(cls, session: Session) -> 'SessionSummary':
        """Create summary from full session.
        
        Args:
            session: Full session object
            
        Returns:
            SessionSummary instance
        """
        return cls(
            session_id=session.session_id,
            user_id=session.user_id,
            agent_id=session.agent_id,
            message_count=len(session.messages),
            created_at=session.created_at,
            updated_at=session.updated_at,
        )


@dataclass
class SessionFilter:
    """Filter criteria for querying sessions."""
    user_id: Optional[str] = None
    agent_id: Optional[str] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    updated_after: Optional[datetime] = None
    updated_before: Optional[datetime] = None
    has_messages: Optional[bool] = None
    
    def matches(self, session: Session) -> bool:
        """Check if a session matches this filter.
        
        Args:
            session: Session to check
            
        Returns:
            True if session matches all filter criteria
        """
        if self.user_id and session.user_id != self.user_id:
            return False
        
        if self.agent_id and session.agent_id != self.agent_id:
            return False
        
        if self.created_after and session.created_at and session.created_at < self.created_after:
            return False
        
        if self.created_before and session.created_at and session.created_at > self.created_before:
            return False
        
        if self.updated_after and session.updated_at and session.updated_at < self.updated_after:
            return False
        
        if self.updated_before and session.updated_at and session.updated_at > self.updated_before:
            return False
        
        if self.has_messages is not None:
            has_msgs = len(session.messages) > 0
            if has_msgs != self.has_messages:
                return False
        
        return True
