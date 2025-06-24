"""Session manager interface for agent session management."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from ..types.content import Message

if TYPE_CHECKING:
    from ..agent.agent import Agent


class SessionManager(ABC):
    """Abstract interface for managing agent sessions.
    
    A session represents a complete interaction context including conversation
    history, user information, agent state, and metadata. This interface provides
    methods to manage sessions and their associated data.
    """
    
    @abstractmethod
    def update_session(self, agent: 'Agent', message: Message) -> None:
        """Update the session with a message and current agent state.
        
        Appends the message to the session's conversation history and updates
        the session with the agent's current state for persistence.
        
        Args:
            agent: Agent instance containing current session state
            message: Message to save to the session
            
        Raises:
            SessionException: If update operation fails
        """
        raise NotImplementedError("Subclasses must implement update_session")
    
    @abstractmethod
    def restore_agent_from_session(self, agent: 'Agent') -> None:
        """Update session data from an agent's current state.
        
        Saves the agent's current conversation history and state back to
        the session storage.
        
        Args:
            agent: Agent instance to save session data from
            
        Raises:
            SessionException: If update operation fails
        """
        raise NotImplementedError("Subclasses must implement update_agent")
