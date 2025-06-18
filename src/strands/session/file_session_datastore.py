


from datetime import datetime
import json
import os
from typing import List, Optional
from strands.session.exceptions import SessionException
from strands.session.models import Session, SessionFilter, SessionSummary
from strands.session.session_datastore import SessionDatastore


class FileSessionDatastore(SessionDatastore):

    def __init__(self, storage_dir: Optional[str] = None):
        # Create the storage directory if it doesn't exist
        self.storage_dir = storage_dir or os.path.join(os.getcwd(), "sessions")
        os.makedirs(self.storage_dir, exist_ok=True)

    def _get_file_path(self, session_id: str) -> str:
        """Get the file path for a session.
        
        Args:
            session_id: The ID of the session.
            
        Returns:
            The file path for the session.
        """
        return os.path.join(self.storage_dir, f"{session_id}.json")
    
    def _read_session_file(self, session_id: str) -> Session:
        """Read session data from file.
        
        Args:
            session_id: The ID of the session to read.
            
        Returns:
            Session object containing session data.
            
        Raises:
            SessionException: If session file doesn't exist or is corrupted.
        """
        file_path = self._get_file_path(session_id)
        
        if not os.path.exists(file_path):
            raise SessionException(f"Session {session_id} does not exist")
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return Session.from_dict(data)
        except json.JSONDecodeError as e:
            raise SessionException(f"Corrupted session file {session_id}: {e}", e)
        except Exception as e:
            raise SessionException(f"Failed to read session {session_id}: {e}", e)
    
    def _write_session_file(self, session: Session) -> None:
        """Write session data to file.
        
        Args:
            session: The session object to write.
            
        Raises:
            SessionException: If write operation fails.
        """
        file_path = self._get_file_path(session.session_id)
        
        # Update timestamp
        session.updated_at = datetime.utcnow()
        
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(session.to_dict(), f, indent=2, ensure_ascii=False)
        except Exception as e:
            raise SessionException(f"Failed to write session {session.session_id}: {e}", e)

    def create_session(self, session: Session) -> None:
        """Create a new session.
        
        Args:
            session: Session object to create
            
        Returns:
            Session identifier for the created session
            
        Raises:
            SessionException: If session creation fails
        """
        # Check if session already exists
        file_path = self._get_file_path(session.session_id)
        if os.path.exists(file_path):
            raise SessionException(f"Session {session.session_id} already exists")
        
        # Save to file
        self._write_session_file(session)
        
        return session
    
    def read_session(self, session_id: str) -> Session:
        """Read current session data.
        
        Returns:
            Session object containing all session data
            
        Raises:
            SessionException: If session doesn't exist or read fails
        """
        return self._read_session_file(session_id)
    
    def update_session(self, session: Session) -> None:
        """Update current session data.
        
        Args:
            session: Updated session object to save
            
        Raises:
            SessionException: If session doesn't exist or update fails
        """
        # Ensure session exists
        self._read_session_file(session.session_id)
        
        # Save to file
        self._write_session_file(session)
    
    def delete_session(self, session_id: str) -> None:
        """Delete the current session.
        
        Raises:
            SessionException: If session doesn't exist or delete fails
        """
        file_path = self._get_file_path(session_id)
        
        if not os.path.exists(file_path):
            raise SessionException(f"Session {session_id} does not exist")
        
        try:
            os.remove(file_path)
        except Exception as e:
            raise SessionException(f"Failed to delete session {self.session_id}: {e}", e)
    
    def list_sessions(self, session_filter: Optional[SessionFilter] = None) -> List[SessionSummary]:
        """List available sessions with optional filtering.
        
        Args:
            session_filter: Optional filter criteria for sessions
            
        Returns:
            List of session summaries that match the filter criteria
            
        Raises:
            SessionException: If list operation fails
        """
        try:
            summaries = []
            for filename in os.listdir(self.storage_dir):
                if filename.endswith('.json'):
                    session_id = filename[:-5]  # Remove .json extension
                    try:
                        session = self._read_session_file(session_id)
                        
                        # Apply filter if provided
                        if session_filter and not session_filter.matches(session):
                            continue
                        
                        summary = SessionSummary.from_session(session)
                        summaries.append(summary)
                    except SessionException:
                        # Skip corrupted or unreadable sessions
                        continue
            
            # Sort by updated_at descending (most recent first)
            summaries.sort(key=lambda s: s.updated_at or datetime.min, reverse=True)
            return summaries
        except Exception as e:
            raise SessionException(f"Failed to list sessions: {e}", e)