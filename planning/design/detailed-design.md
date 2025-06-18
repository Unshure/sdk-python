# Detailed Design: Persistence Feature for Strands Agents SDK

## Overview

This document provides a comprehensive design for implementing a persistence feature in the Strands Agents SDK. The feature will enable automatic saving and restoration of agent state, customer state, and request state to ensure continuity across agent restarts.

## Requirements

Based on the requirements clarification, the persistence system must:

1. **State Persistence**: Store three types of state:
   - Agent state: conversation history (messages)
   - Customer state: JSON-serializable dictionary
   - Request state: latest message, event_loop_metrics, stop_reason

2. **Automatic Operation**: 
   - Save state on every message (on_message_received and agent response)
   - Automatically restore state when persistence implementation is provided during initialization

3. **Backend Agnostic**: Provide interface for different storage backends with file-based implementation as starting point

4. **Session Management**: Identify sessions using session_id + agent_id + user_id combination

5. **Error Handling**: Throw exceptions on save failures and corrupted data during recovery

6. **Integration**: Built into core Agent class as new initialization parameter, implemented via callback_handler

## Architecture

### High-Level Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│     Agent       │    │ PersistenceManager│    │ Storage Backend │
│                 │    │   (Interface)     │    │ (File/DB/etc.)  │
│ - persistence   │───▶│                   │───▶│                 │
│ - callback      │    │ - save_*_state()  │    │ - JSON files    │
│ - messages      │    │ - load_*_state()  │    │ - Database      │
│ - customer_state│    │ - delete_*()      │    │ - Cloud storage │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │
         │              ┌────────▼────────┐
         │              │ PersistenceCallback│
         └─────────────▶│    Handler      │
                        │                 │
                        │ - on_message    │
                        │ - on_response   │
                        └─────────────────┘
```

### Component Relationships

1. **Agent Class**: Extended with persistence_manager parameter and customer_state attribute
2. **PersistenceManager**: Abstract interface for backend-agnostic persistence operations
3. **FilePersistenceManager**: File-based implementation of PersistenceManager
4. **PersistenceCallbackHandler**: Handles automatic persistence via callback events
5. **Storage Backend**: Pluggable storage implementations (files, databases, etc.)

## Components and Interfaces

### 1. PersistenceManager Interface

```python
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Any, Optional
from ..types.content import Message
from ..telemetry.metrics import EventLoopMetrics
from ..types.streaming import StopReason

class PersistenceManager(ABC):
    """Abstract interface for persisting agent state across sessions."""
    
    @abstractmethod
    def save_agent_state(self, session_id: str, agent_id: str, user_id: str, 
                        messages: List[Message]) -> None:
        """Save agent conversation history.
        
        Args:
            session_id: Unique session identifier
            agent_id: Unique agent identifier  
            user_id: Unique user identifier
            messages: List of conversation messages
            
        Raises:
            PersistenceException: If save operation fails
        """
        pass
    
    @abstractmethod
    def save_customer_state(self, session_id: str, agent_id: str, user_id: str, 
                           state: Dict[str, Any]) -> None:
        """Save customer-specific state data.
        
        Args:
            session_id: Unique session identifier
            agent_id: Unique agent identifier
            user_id: Unique user identifier
            state: JSON-serializable customer state dictionary
            
        Raises:
            PersistenceException: If save operation fails
        """
        pass
    
    @abstractmethod
    def save_request_state(self, session_id: str, agent_id: str, user_id: str,
                          message: Message, metrics: EventLoopMetrics, 
                          stop_reason: StopReason) -> None:
        """Save current request execution state.
        
        Args:
            session_id: Unique session identifier
            agent_id: Unique agent identifier
            user_id: Unique user identifier
            message: Latest agent message
            metrics: Event loop performance metrics
            stop_reason: Reason for stopping execution
            
        Raises:
            PersistenceException: If save operation fails
        """
        pass
    
    @abstractmethod
    def load_agent_state(self, session_id: str, agent_id: str, user_id: str) -> List[Message]:
        """Load agent conversation history.
        
        Args:
            session_id: Unique session identifier
            agent_id: Unique agent identifier
            user_id: Unique user identifier
            
        Returns:
            List of conversation messages, empty if no previous state
            
        Raises:
            PersistenceException: If data is corrupted or load fails
        """
        pass
    
    @abstractmethod
    def load_customer_state(self, session_id: str, agent_id: str, user_id: str) -> Dict[str, Any]:
        """Load customer-specific state data.
        
        Args:
            session_id: Unique session identifier
            agent_id: Unique agent identifier
            user_id: Unique user identifier
            
        Returns:
            Customer state dictionary, empty if no previous state
            
        Raises:
            PersistenceException: If data is corrupted or load fails
        """
        pass
    
    @abstractmethod
    def load_request_state(self, session_id: str, agent_id: str, user_id: str) -> Optional[Tuple[Message, EventLoopMetrics, StopReason]]:
        """Load current request execution state.
        
        Args:
            session_id: Unique session identifier
            agent_id: Unique agent identifier
            user_id: Unique user identifier
            
        Returns:
            Tuple of (message, metrics, stop_reason) or None if no previous state
            
        Raises:
            PersistenceException: If data is corrupted or load fails
        """
        pass
    
    @abstractmethod
    def delete_session(self, session_id: str, agent_id: str, user_id: str) -> None:
        """Delete all persisted data for a session.
        
        Args:
            session_id: Unique session identifier
            agent_id: Unique agent identifier
            user_id: Unique user identifier
            
        Raises:
            PersistenceException: If delete operation fails
        """
        pass
    
    @abstractmethod
    def session_exists(self, session_id: str, agent_id: str, user_id: str) -> bool:
        """Check if a session has persisted data.
        
        Args:
            session_id: Unique session identifier
            agent_id: Unique agent identifier
            user_id: Unique user identifier
            
        Returns:
            True if session data exists, False otherwise
        """
        pass
```

### 2. FilePersistenceManager Implementation

```python
import json
import os
import tempfile
from dataclasses import asdict
from typing import Dict, List, Tuple, Any, Optional
from .persistence_manager import PersistenceManager
from ..types.content import Message
from ..telemetry.metrics import EventLoopMetrics
from ..types.streaming import StopReason

class FilePersistenceManager(PersistenceManager):
    """File-based implementation of PersistenceManager."""
    
    def __init__(self, storage_dir: Optional[str] = None):
        """Initialize file-based persistence manager.
        
        Args:
            storage_dir: Directory for storing persistence files.
                        Defaults to system temp directory if None.
        """
        self.storage_dir = storage_dir or tempfile.gettempdir()
        os.makedirs(self.storage_dir, exist_ok=True)
    
    def _get_session_dir(self, session_id: str, agent_id: str, user_id: str) -> str:
        """Get directory path for a specific session."""
        session_key = f"{session_id}_{agent_id}_{user_id}"
        return os.path.join(self.storage_dir, session_key)
    
    def _ensure_session_dir(self, session_id: str, agent_id: str, user_id: str) -> str:
        """Ensure session directory exists and return path."""
        session_dir = self._get_session_dir(session_id, agent_id, user_id)
        os.makedirs(session_dir, exist_ok=True)
        return session_dir
    
    def save_agent_state(self, session_id: str, agent_id: str, user_id: str, 
                        messages: List[Message]) -> None:
        """Save agent conversation history to file."""
        try:
            session_dir = self._ensure_session_dir(session_id, agent_id, user_id)
            file_path = os.path.join(session_dir, "agent_state.json")
            
            with open(file_path, 'w') as f:
                json.dump(messages, f, indent=2)
        except Exception as e:
            raise PersistenceException(f"Failed to save agent state: {e}") from e
    
    def save_customer_state(self, session_id: str, agent_id: str, user_id: str, 
                           state: Dict[str, Any]) -> None:
        """Save customer state to file."""
        try:
            session_dir = self._ensure_session_dir(session_id, agent_id, user_id)
            file_path = os.path.join(session_dir, "customer_state.json")
            
            with open(file_path, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            raise PersistenceException(f"Failed to save customer state: {e}") from e
    
    def save_request_state(self, session_id: str, agent_id: str, user_id: str,
                          message: Message, metrics: EventLoopMetrics, 
                          stop_reason: StopReason) -> None:
        """Save request state to file."""
        try:
            session_dir = self._ensure_session_dir(session_id, agent_id, user_id)
            file_path = os.path.join(session_dir, "request_state.json")
            
            request_state = {
                "message": message,
                "metrics": asdict(metrics),
                "stop_reason": stop_reason
            }
            
            with open(file_path, 'w') as f:
                json.dump(request_state, f, indent=2)
        except Exception as e:
            raise PersistenceException(f"Failed to save request state: {e}") from e
    
    def load_agent_state(self, session_id: str, agent_id: str, user_id: str) -> List[Message]:
        """Load agent conversation history from file."""
        try:
            session_dir = self._get_session_dir(session_id, agent_id, user_id)
            file_path = os.path.join(session_dir, "agent_state.json")
            
            if not os.path.exists(file_path):
                return []
            
            with open(file_path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise PersistenceException(f"Corrupted agent state data: {e}") from e
        except Exception as e:
            raise PersistenceException(f"Failed to load agent state: {e}") from e
    
    def load_customer_state(self, session_id: str, agent_id: str, user_id: str) -> Dict[str, Any]:
        """Load customer state from file."""
        try:
            session_dir = self._get_session_dir(session_id, agent_id, user_id)
            file_path = os.path.join(session_dir, "customer_state.json")
            
            if not os.path.exists(file_path):
                return {}
            
            with open(file_path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise PersistenceException(f"Corrupted customer state data: {e}") from e
        except Exception as e:
            raise PersistenceException(f"Failed to load customer state: {e}") from e
    
    def load_request_state(self, session_id: str, agent_id: str, user_id: str) -> Optional[Tuple[Message, EventLoopMetrics, StopReason]]:
        """Load request state from file."""
        try:
            session_dir = self._get_session_dir(session_id, agent_id, user_id)
            file_path = os.path.join(session_dir, "request_state.json")
            
            if not os.path.exists(file_path):
                return None
            
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Reconstruct EventLoopMetrics from dict
            metrics_data = data["metrics"]
            metrics = EventLoopMetrics(**metrics_data)
            
            return (data["message"], metrics, data["stop_reason"])
        except json.JSONDecodeError as e:
            raise PersistenceException(f"Corrupted request state data: {e}") from e
        except Exception as e:
            raise PersistenceException(f"Failed to load request state: {e}") from e
```

### 3. PersistenceCallbackHandler

```python
from typing import Any, Dict, Optional
from ..handlers.callback_handler import CompositeCallbackHandler
from .persistence_manager import PersistenceManager
from ..types.content import Message
from ..telemetry.metrics import EventLoopMetrics
from ..types.streaming import StopReason

class PersistenceCallbackHandler:
    """Callback handler that automatically persists agent state."""
    
    def __init__(self, persistence_manager: PersistenceManager, 
                 session_id: str, agent_id: str, user_id: str):
        """Initialize persistence callback handler.
        
        Args:
            persistence_manager: Persistence implementation to use
            session_id: Session identifier
            agent_id: Agent identifier
            user_id: User identifier
        """
        self.persistence_manager = persistence_manager
        self.session_id = session_id
        self.agent_id = agent_id
        self.user_id = user_id
    
    def __call__(self, **kwargs: Any) -> None:
        """Handle callback events and persist relevant data."""
        # Save message when received
        if "message" in kwargs:
            message = kwargs["message"]
            # This will be called from Agent context where we have access to messages
            # We'll need to pass the full message list through the callback
            if "messages" in kwargs:
                messages = kwargs["messages"]
                self.persistence_manager.save_agent_state(
                    self.session_id, self.agent_id, self.user_id, messages
                )
        
        # Save request state when available
        if all(key in kwargs for key in ["latest_message", "event_loop_metrics", "stop_reason"]):
            self.persistence_manager.save_request_state(
                self.session_id, self.agent_id, self.user_id,
                kwargs["latest_message"], 
                kwargs["event_loop_metrics"], 
                kwargs["stop_reason"]
            )
        
        # Save customer state when updated
        if "customer_state" in kwargs:
            self.persistence_manager.save_customer_state(
                self.session_id, self.agent_id, self.user_id, 
                kwargs["customer_state"]
            )
```

### 4. Agent Class Extensions

```python
# Extensions to the existing Agent class

class Agent:
    def __init__(
        self,
        # ... existing parameters ...
        persistence_manager: Optional[PersistenceManager] = None,
        session_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        user_id: Optional[str] = None,
        # ... rest of parameters ...
    ):
        # ... existing initialization ...
        
        # Persistence setup
        self.persistence_manager = persistence_manager
        self.session_id = session_id
        self.agent_id = agent_id or f"agent_{uuid4().hex[:8]}"
        self.user_id = user_id
        self.customer_state: Dict[str, Any] = {}
        
        # Auto-restore state if persistence is enabled
        if self.persistence_manager and all([self.session_id, self.agent_id, self.user_id]):
            self._restore_persisted_state()
        
        # Setup persistence callback handler
        if self.persistence_manager:
            persistence_callback = PersistenceCallbackHandler(
                self.persistence_manager, self.session_id, self.agent_id, self.user_id
            )
            self.callback_handler = CompositeCallbackHandler(
                self.callback_handler, persistence_callback
            )
    
    def _restore_persisted_state(self) -> None:
        """Restore agent state from persistence if available."""
        try:
            # Restore conversation history
            persisted_messages = self.persistence_manager.load_agent_state(
                self.session_id, self.agent_id, self.user_id
            )
            if persisted_messages:
                self.messages = persisted_messages
            
            # Restore customer state
            self.customer_state = self.persistence_manager.load_customer_state(
                self.session_id, self.agent_id, self.user_id
            )
            
            # Note: Request state restoration handled separately as it's context-specific
        except Exception as e:
            # Re-raise as required by specifications
            raise PersistenceException(f"Failed to restore persisted state: {e}") from e
    
    def update_customer_state(self, updates: Dict[str, Any]) -> None:
        """Update customer state and persist changes."""
        self.customer_state.update(updates)
        if self.persistence_manager:
            self.persistence_manager.save_customer_state(
                self.session_id, self.agent_id, self.user_id, self.customer_state
            )
    
    def get_customer_state(self) -> Dict[str, Any]:
        """Get current customer state."""
        return self.customer_state.copy()
    
    def clear_session(self) -> None:
        """Clear all persisted data for current session."""
        if self.persistence_manager:
            self.persistence_manager.delete_session(
                self.session_id, self.agent_id, self.user_id
            )
        self.messages.clear()
        self.customer_state.clear()
```

## Data Models

### 1. Exception Classes

```python
class PersistenceException(Exception):
    """Exception raised when persistence operations fail."""
    pass
```

### 2. Session Identifier

```python
from dataclasses import dataclass

@dataclass
class SessionIdentifier:
    """Composite identifier for a persistence session."""
    session_id: str
    agent_id: str
    user_id: str
    
    def __str__(self) -> str:
        return f"{self.session_id}_{self.agent_id}_{self.user_id}"
```

## Error Handling

### 1. Save Operation Failures
- **Requirement**: Throw exceptions on save failures
- **Implementation**: All save methods wrap operations in try-catch and raise `PersistenceException`
- **Recovery**: No automatic recovery - caller must handle exceptions

### 2. Load Operation Failures
- **Corrupted Data**: Throw `PersistenceException` with specific error details
- **Missing Data**: Return empty/default values (empty list, empty dict, None)
- **File System Errors**: Throw `PersistenceException`

### 3. Session Management Errors
- **Invalid Identifiers**: Validate session identifiers and raise appropriate exceptions
- **Permission Issues**: Wrap and re-raise as `PersistenceException`

## Testing Strategy

### 1. Unit Tests
- **PersistenceManager Interface**: Test all abstract methods
- **FilePersistenceManager**: Test file operations, error conditions, data integrity
- **PersistenceCallbackHandler**: Test callback event handling
- **Agent Integration**: Test initialization, restoration, state updates

### 2. Integration Tests
- **End-to-End Persistence**: Create agent, interact, restart, verify state restoration
- **Error Scenarios**: Test corrupted files, permission issues, disk full conditions
- **Concurrent Access**: Verify single-agent assumption holds

### 3. Performance Tests
- **Large Conversations**: Test with extensive message histories
- **Frequent Updates**: Test rapid state changes and persistence
- **Storage Efficiency**: Verify file sizes and storage patterns

## Implementation Notes

### 1. Backward Compatibility
- New persistence features are optional (default None parameters)
- Existing Agent functionality unchanged when persistence not enabled
- Can coexist with existing ConversationManager

### 2. Thread Safety
- Single agent instance assumption eliminates concurrency concerns
- File operations use atomic writes where possible
- No explicit locking required based on requirements

### 3. Storage Efficiency
- JSON format for human readability and debugging
- Separate files for different state types enable partial updates
- Directory structure supports easy cleanup and management

### 4. Extensibility
- Abstract interface supports multiple backend implementations
- Plugin architecture for custom storage solutions
- Configuration options for storage behavior customization
