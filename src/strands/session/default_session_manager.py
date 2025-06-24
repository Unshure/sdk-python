"""File-based implementation of session manager."""

import json
import os
from datetime import datetime
from typing import Any, List, Optional, TYPE_CHECKING
from uuid import uuid4

from strands.session.file_session_datastore import FileSessionDatastore

from .exceptions import SessionException
from .models import Session, SessionSummary, SessionFilter
from .session_manager import SessionManager

if TYPE_CHECKING:
    from ..agent.agent import Agent


class DefaultSessionManager(SessionManager):
    """Default implementation of session manager.
    
    This implementation stores sessions as JSON files in a specified directory.
    Each session is stored in a separate file named by its session_id.
    """
    
    def __init__(self,
                 session_id: str = str(uuid4()),
                 user_id: str = str(uuid4()),
                 agent_id: str = str(uuid4()),
                 session_datastore: FileSessionDatastore = FileSessionDatastore()):
        """Initialize the FileSessionManager.
        
        Args:
            session_id: ID of the session to manage. If None, a new session will be created.
            storage_dir: Directory where session files will be stored.
                If None, defaults to a 'sessions' directory in the current working directory.
        """
        self.session_datastore = session_datastore

        try:
            # Try to read existing session
            session = self.session_datastore.read_session(session_id)
        except SessionException:
            # Session doesn't exist, create new one
            session = Session(
                session_id=session_id,
                user_id=user_id,
                agent_id=agent_id,
                messages=[],
            )
            self.session_datastore.create_session(session)

        self.session = session
    
    
    def update_session(self, agent: 'Agent', message: Any) -> None:
        """Update the session with a message and current agent state.
        
        Args:
            agent: Agent instance containing current session state
            message: Message to save to the session
            
        Raises:
            SessionException: If update operation fails
        """      
        # Add the message
        self.session.add_message(message)
        
        # Update session state from agent state
        if hasattr(agent, 'state') and hasattr(agent.state, 'get_all'):
            self.session.state = agent.state.get_all()
        
        # Save to file
        self.session_datastore.update_session(self.session)
    
    def save_message(self, agent: 'Agent', message: Any) -> None:
        """Save a single message to the current session.
        
        Deprecated: Use update_session() instead for unified message and state persistence.
        
        Args:
            agent: Agent instance containing current session state
            message: Message to save to the session
            
        Raises:
            SessionException: If save operation fails
        """      
        # Delegate to update_session for backward compatibility
        self.update_session(agent, message)
    
    def restore_agent_from_session(self, agent: 'Agent') -> None:
        """Restore agent data from the current session.
        
        Args:
            agent: Agent instance to restore session data to
            
        Raises:
            SessionException: If restore operation fails
        """
        # Restore messages
        agent.messages = self.session.messages.copy()
        
        # Restore state if agent has state management and session has state
        if hasattr(agent, 'state') and hasattr(agent.state, 'set') and self.session.state:
            # Clear existing state
            for namespace in agent.state.list_namespaces():
                agent.state.clear(namespace=namespace)
            
            # Restore state from session
            for namespace_name, namespace_data in self.session.state.items():
                for key, value in namespace_data.items():
                    agent.state.set(key, value, namespace=namespace_name)

