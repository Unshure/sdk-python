# Research: Existing Persistence Implementation

## Overview
This document analyzes the existing conversation persistence POC implementation from commit 304cf47.

## Files Modified/Added
Based on git commit analysis, the following files were involved in the persistence POC:
- `src/strands/agent/agent.py` - Main agent class modifications
- `src/strands/agent/conversation_manager/__init__.py` - New conversation manager module
- `src/strands/agent/conversation_manager/conversation_manager.py` - Abstract interface
- `src/strands/agent/conversation_manager/file_conversation_manager.py` - File-based implementation
- `src/strands/agent/conversation_manager/test_file_conversation_manager.py` - Tests
- `test_file_conversation.py` - Integration test

## Analysis of Current Implementation

### 1. ConversationManager Abstract Interface
- Provides abstract base class for conversation management
- Main methods: `apply_management()`, `reduce_context()`, `save_message()`, `load_conversation()`
- Optional persistence methods: `save_message()` and `load_conversation()`
- Designed primarily for conversation history management and context window control

### 2. FileConversationManager Implementation
- Extends ConversationManager with file-based persistence
- Stores conversations as JSON files in configurable directory
- Each conversation stored in separate file named by conversation_id
- Includes duplicate message detection to avoid redundant saves
- Stores: conversation_id, agent_id, messages, and optional state

### 3. Agent Integration
- Agent constructor accepts optional `conversation_manager` parameter
- Defaults to `SlidingWindowConversationManager` if not provided
- Persistence integrated via callback handlers and direct calls to `save_message()`
- Messages saved at multiple points: user input, assistant responses, tool calls

### 4. Current Data Structure
```python
class Conversation(TypedDict):
    conversation_id: str
    agent_id: str
    messages: List["Message"]
    state: Optional[dict]
```

## Gaps Identified for New Requirements

### 1. Missing State Types
Current implementation only stores:
- ✅ Conversation history (messages)
- ✅ Basic state (generic dict)

Missing:
- ❌ Request state (event_loop_metrics, stop_reason, latest message)
- ❌ Customer state (separate from generic state)

### 2. Identification System
Current system uses:
- conversation_id (UUID)
- agent_id (UUID-based)

Required system needs:
- session_id + agent_id + user_id combination

### 3. Callback Integration
Current implementation:
- Uses direct calls to `save_message()` in various Agent methods
- Has some callback handler integration but not comprehensive

Required:
- Full callback handler integration for all persistence events
- Save on `on_message_received` and agent response events

### 4. Interface Design
Current interface is conversation-focused, but requirements need:
- Backend-agnostic persistence interface
- CRUD operations
- Support for multiple state types
- Automatic restoration on initialization

## Recommendations for Enhancement

1. **Extend the interface** to support multiple state types and CRUD operations
2. **Refactor identification** to use session_id + agent_id + user_id
3. **Implement comprehensive callback integration** for all persistence events
4. **Add request state tracking** for event_loop_metrics and stop_reason
5. **Separate customer state** from generic state storage
6. **Add automatic restoration** logic during agent initialization
