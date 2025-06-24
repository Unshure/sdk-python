# Strands Agents Data Models

## Core Data Models

### Message
Represents a message in a conversation between the user and the assistant.

```python
class Message:
    role: str  # "user", "assistant", "system", "tool"
    content: Union[str, List[ContentItem]]
    name: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None
    tool_call_id: Optional[str] = None
```

### ContentItem
Represents a content item in a message, which can be text or other media.

```python
class ContentItem:
    type: str  # "text", "image", etc.
    text: Optional[str] = None
    image_url: Optional[ImageUrl] = None
```

### ImageUrl
Represents an image URL in a content item.

```python
class ImageUrl:
    url: str
```

### ToolCall
Represents a tool call in a model response.

```python
class ToolCall:
    id: str
    name: str
    arguments: Dict[str, Any]
```

### ModelResponse
Represents a response from a model.

```python
class ModelResponse:
    content: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None
    stop_reason: Optional[str] = None
```

### ModelResponseChunk
Represents a chunk of a streaming model response.

```python
class ModelResponseChunk:
    content: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None
    stop_reason: Optional[str] = None
    is_finished: bool = False
```

### AgentResult
Represents the result of an agent operation.

```python
class AgentResult:
    content: str
    tool_calls: List[Dict[str, Any]]
    raw_response: Any
```

### Tool
Represents a tool that can be used by the agent.

```python
class Tool:
    name: str
    description: str
    parameters: Dict[str, Any]
    function: Callable
```

### EventLoopState
Represents the state of the event loop.

```python
class EventLoopState:
    messages: List[Message]
    model: Model
    tools: List[Tool]
    tool_handler: ToolHandler
    callback_handler: CallbackHandler
    metrics: Optional[EventLoopMetrics] = None
    trace_provider: Optional[TraceProvider] = None
```

## Model Provider Data Models

### BedrockModelParameters
Parameters for the Bedrock model provider.

```python
class BedrockModelParameters:
    model_id: str
    region: Optional[str] = None
    endpoint_url: Optional[str] = None
    profile_name: Optional[str] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    top_k: Optional[int] = None
    max_tokens: Optional[int] = None
    stop_sequences: Optional[List[str]] = None
    streaming: bool = False
```

### AnthropicModelParameters
Parameters for the Anthropic model provider.

```python
class AnthropicModelParameters:
    model_id: str
    api_key: Optional[str] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    top_k: Optional[int] = None
    max_tokens: Optional[int] = None
    stop_sequences: Optional[List[str]] = None
    streaming: bool = False
```

### OpenAIModelParameters
Parameters for the OpenAI model provider.

```python
class OpenAIModelParameters:
    model_id: str
    api_key: Optional[str] = None
    organization: Optional[str] = None
    base_url: Optional[str] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    max_tokens: Optional[int] = None
    stop: Optional[Union[str, List[str]]] = None
    streaming: bool = False
```

## Tool Data Models

### MCPToolParameters
Parameters for MCP tools.

```python
class MCPToolParameters:
    name: str
    description: str
    parameters: Dict[str, Any]
```

### MCPToolResponse
Response from an MCP tool.

```python
class MCPToolResponse:
    content: Any
    error: Optional[str] = None
```

## Telemetry Data Models

### EventLoopMetrics
Metrics for the event loop.

```python
class EventLoopMetrics:
    total_tokens: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_cost: float = 0
    start_time: Optional[float] = None
    end_time: Optional[float] = None
```

### TraceContext
Context for tracing operations.

```python
class TraceContext:
    trace_id: str
    span_id: str
    parent_id: Optional[str] = None
```
