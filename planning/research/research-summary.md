# Research Summary: Persistence Feature Implementation

## Overview
This document summarizes the research findings for implementing the persistence feature in the Strands Agents SDK.

## Key Findings

### 1. Existing Implementation Analysis
- **Current POC**: FileConversationManager provides basic conversation persistence
- **Integration**: Already integrated into Agent class via conversation_manager parameter
- **Limitations**: Only handles conversation history, lacks request state and customer state tracking
- **Architecture**: Uses abstract ConversationManager interface with file-based implementation

### 2. Data Model Compatibility
All required data types are JSON serializable:

#### Agent State (Conversation History)
- ✅ `List[Message]` - TypedDict structures, fully JSON serializable
- ✅ Already implemented in current POC

#### Customer State
- ✅ `Dict[str, Any]` - JSON serializable dictionary
- ✅ Simple to implement

#### Request State Components
- ✅ `Message` - TypedDict, JSON serializable
- ✅ `EventLoopMetrics` - @dataclass with basic types (int, float, dict, list)
- ✅ `StopReason` - Literal string type, JSON serializable

### 3. Callback Handler Integration Points
Current callback events available:
- `callback_handler(message=message)` - Perfect for message persistence
- `callback_handler(start_event_loop=True)` - Event loop initialization
- `callback_handler(start=True)` - General start events

### 4. Session Identification
Current system uses:
- `conversation_id` (UUID)
- `agent_id` (UUID-based)

Required system needs:
- `session_id + agent_id + user_id` combination

## Architecture Recommendations

### 1. New Persistence Interface
Create a new `PersistenceManager` interface separate from `ConversationManager`:

```python
class PersistenceManager(ABC):
    @abstractmethod
    def save_agent_state(self, session_id: str, agent_id: str, user_id: str, messages: List[Message]) -> None
    
    @abstractmethod
    def save_customer_state(self, session_id: str, agent_id: str, user_id: str, state: Dict[str, Any]) -> None
    
    @abstractmethod
    def save_request_state(self, session_id: str, agent_id: str, user_id: str, 
                          message: Message, metrics: EventLoopMetrics, stop_reason: StopReason) -> None
    
    @abstractmethod
    def load_agent_state(self, session_id: str, agent_id: str, user_id: str) -> List[Message]
    
    @abstractmethod
    def load_customer_state(self, session_id: str, agent_id: str, user_id: str) -> Dict[str, Any]
    
    @abstractmethod
    def load_request_state(self, session_id: str, agent_id: str, user_id: str) -> Tuple[Message, EventLoopMetrics, StopReason]
```

### 2. Integration Strategy
- **Agent Parameter**: Add `persistence_manager: Optional[PersistenceManager]` to Agent constructor
- **Callback Integration**: Implement as specialized callback handler
- **Automatic Restoration**: Load state during Agent initialization if persistence_manager provided
- **Default Storage**: Use temp directory with customizable path

### 3. File-Based Implementation
Extend current file-based approach:
- **Directory Structure**: `{storage_dir}/{session_id}_{agent_id}_{user_id}/`
- **Files**: 
  - `agent_state.json` (conversation history)
  - `customer_state.json` (customer data)
  - `request_state.json` (latest request state)

### 4. Error Handling
- **Save Failures**: Throw exceptions (as required)
- **Load Failures**: Throw exceptions for corrupted data (as required)
- **Missing Data**: Return empty/default values for new sessions

## Implementation Plan Insights

### 1. Leverage Existing Code
- Build upon current ConversationManager architecture
- Reuse file-based storage patterns from FileConversationManager
- Extend Agent class integration patterns

### 2. Callback Handler Strategy
- Create `PersistenceCallbackHandler` that implements the persistence logic
- Integrate with existing CompositeCallbackHandler pattern
- Hook into `message=message` events for automatic persistence

### 3. Serialization Strategy
- Use JSON for all persistence (all types are compatible)
- Handle dataclass serialization with `asdict()` for EventLoopMetrics
- Direct JSON serialization for TypedDict structures

### 4. Session Management
- Implement session identification outside the interface (as required)
- Allow external systems to provide session_id, agent_id, user_id
- Support both new session creation and existing session restoration

## Next Steps
1. Create detailed design document based on these findings
2. Design the new PersistenceManager interface
3. Plan the integration with existing Agent architecture
4. Develop implementation plan with incremental steps
