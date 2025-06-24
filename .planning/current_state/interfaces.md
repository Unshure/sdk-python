# Strands Agents Interfaces

## Core Interfaces

### Agent Interface
The primary entry point for interacting with the SDK.

```python
class Agent:
    def __init__(
        self,
        model=None,
        tools=None,
        conversation_manager=None,
        callback_handler=None,
        tool_handler=None,
        event_loop_metrics=None,
        trace_provider=None,
    ): ...
    
    def __call__(self, message, **kwargs): ...
    
    async def acall(self, message, **kwargs): ...
    
    def stream(self, message, **kwargs): ...
    
    async def astream(self, message, **kwargs): ...
```

### Model Interface
Base interface for all model providers.

```python
class Model:
    async def generate(
        self,
        messages: List[Message],
        tools: Optional[List[Tool]] = None,
        **kwargs
    ) -> ModelResponse: ...
    
    async def generate_stream(
        self,
        messages: List[Message],
        tools: Optional[List[Tool]] = None,
        **kwargs
    ) -> AsyncIterator[ModelResponseChunk]: ...
```

### Tool Interface
Interface for defining tools that extend agent capabilities.

```python
@tool
def my_tool(param1: str, param2: int) -> str:
    """Tool description.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Description of return value
    """
    ...
```

### Conversation Manager Interface
Interface for managing conversation history.

```python
class ConversationManager:
    def add_user_message(self, content: str) -> None: ...
    
    def add_assistant_message(self, content: str) -> None: ...
    
    def get_messages(self) -> List[Message]: ...
    
    def clear(self) -> None: ...
```

### Callback Handler Interface
Interface for monitoring and customizing agent behavior.

```python
class CallbackHandler:
    def on_tool_start(self, tool_name: str, tool_input: Any) -> None: ...
    
    def on_tool_end(self, tool_name: str, tool_output: Any) -> None: ...
    
    def on_tool_error(self, tool_name: str, error: Exception) -> None: ...
    
    def on_llm_start(self, model: str, prompt: str) -> None: ...
    
    def on_llm_end(self, model: str, response: str) -> None: ...
    
    def on_llm_error(self, model: str, error: Exception) -> None: ...
    
    def on_chain_start(self) -> None: ...
    
    def on_chain_end(self) -> None: ...
    
    def on_chain_error(self, error: Exception) -> None: ...
```

### MCP Client Interface
Interface for interacting with Model Context Protocol servers.

```python
class MCPClient:
    def __init__(self, client_factory): ...
    
    def __enter__(self): ...
    
    def __exit__(self, exc_type, exc_val, exc_tb): ...
    
    def list_tools_sync(self) -> List[Tool]: ...
    
    async def list_tools(self) -> List[Tool]: ...
```

## Message Formats

### Message
Represents a message in a conversation.

```python
class Message:
    role: str  # "user", "assistant", "system", "tool"
    content: Union[str, List[ContentItem]]
    name: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None
    tool_call_id: Optional[str] = None
```

### ModelResponse
Represents a response from a model.

```python
class ModelResponse:
    content: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None
    stop_reason: Optional[str] = None
```

### ToolCall
Represents a tool call in a model response.

```python
class ToolCall:
    id: str
    name: str
    arguments: Dict[str, Any]
```

## Event Loop Types

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

## Tool Types

### Tool
Represents a tool that can be used by the agent.

```python
class Tool:
    name: str
    description: str
    parameters: Dict[str, Any]
    function: Callable
```

### ToolRegistry
Registry for managing tools.

```python
class ToolRegistry:
    @staticmethod
    def register(func=None, *, name=None, description=None): ...
    
    @staticmethod
    def get_tools() -> List[Tool]: ...
```
