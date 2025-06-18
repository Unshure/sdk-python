# Research: Data Models and Callback Handler Analysis

## Overview
This document analyzes the current data models and callback handler interface to understand what needs to be persisted and how to integrate with the callback system.

## Current Data Models Analysis

### 1. Message Structure
```python
class Message(TypedDict):
    content: List[ContentBlock]
    role: Role  # Literal["user", "assistant"]
```

### 2. ContentBlock Structure
```python
class ContentBlock(TypedDict, total=False):
    cachePoint: CachePoint
    document: DocumentContent
    guardContent: GuardContent
    image: ImageContent
    reasoningContent: ReasoningContentBlock
    text: str
    toolResult: ToolResult
    toolUse: ToolUse
    video: VideoContent
```

### 3. AgentResult Structure
```python
@dataclass
class AgentResult:
    stop_reason: StopReason
    message: Message
    metrics: EventLoopMetrics
    state: Any
```

## Callback Handler Events Analysis

Based on event_loop.py analysis, the following callback events are triggered:

### Current Callback Events:
1. `callback_handler(start=True)` - Event loop start
2. `callback_handler(start_event_loop=True)` - Event loop initialization
3. `callback_handler(message=message)` - When a message is added to conversation
4. `callback_handler(force_stop=True, force_stop_reason=str(e))` - On exceptions
5. `callback_handler(message=tool_result_message)` - When tool results are processed

### Streaming Events:
- `callback_handler(data=text, complete=False/True)` - Streaming text
- `callback_handler(reasoningText=text)` - Reasoning text
- `callback_handler(current_tool_use=tool_info)` - Tool usage info

## Data Serialization Requirements

### 1. Agent State (Conversation History)
- **Current**: List[Message] - already JSON serializable via TypedDict
- **Status**: ✅ Ready for persistence

### 2. Customer State
- **Required**: Python dictionary (JSON serializable object)
- **Status**: ✅ Simple dict serialization

### 3. Request State
- **Required Components**:
  - Latest agent message: Message (already serializable)
  - event_loop_metrics: EventLoopMetrics (needs analysis)
  - stop_reason: StopReason (needs analysis)

### 4. EventLoopMetrics Analysis
Need to examine EventLoopMetrics structure for serialization:

```python
# From telemetry/metrics.py - needs investigation
class EventLoopMetrics:
    # Contains performance and usage metrics
    # Need to check if JSON serializable
```

### 5. StopReason Analysis
Need to examine StopReason type:

```python
# From types/streaming.py - needs investigation
StopReason = ...  # Need to check definition
```

## Integration Points for Persistence

### 1. Callback Handler Integration
- **Current**: Direct calls to `save_message()` in Agent methods
- **Required**: Full callback handler integration
- **Events to Hook**: 
  - `message=message` events for all message persistence
  - Need custom events for request state and customer state

### 2. Agent Initialization
- **Current**: Optional conversation_manager parameter
- **Required**: New persistence parameter with automatic restoration

### 3. State Management
- **Current**: Single state dict in conversation
- **Required**: Separate tracking of agent, customer, and request state

## Recommendations

1. **Investigate EventLoopMetrics and StopReason** for JSON serialization compatibility
2. **Design new callback events** for request state and customer state persistence
3. **Create comprehensive persistence interface** that extends beyond conversation management
4. **Implement automatic restoration logic** during agent initialization
5. **Design session identification system** using session_id + agent_id + user_id
