# Strands Agents SDK Documentation

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Components](#components)
4. [Interfaces](#interfaces)
5. [Data Models](#data-models)
6. [Workflows](#workflows)
7. [Dependencies](#dependencies)
8. [Codebase Overview](#codebase-overview)

## Overview

Strands Agents is a simple yet powerful SDK that takes a model-driven approach to building and running AI agents. From simple conversational assistants to complex autonomous workflows, from local development to production deployment, Strands Agents scales with your needs.

### Key Features

- **Lightweight & Flexible**: Simple agent loop that just works and is fully customizable
- **Model Agnostic**: Support for Amazon Bedrock, Anthropic, LiteLLM, Llama, Ollama, OpenAI, and custom providers
- **Advanced Capabilities**: Multi-agent systems, autonomous agents, and streaming support
- **Built-in MCP**: Native support for Model Context Protocol (MCP) servers, enabling access to thousands of pre-built tools

### Repository Structure

- **src/strands**: Main source code directory
- **tests**: Unit tests
- **tests-integ**: Integration tests
- **tools**: Development tools
- **build**: Build artifacts
- **.github**: GitHub workflows and configuration
- **.venv**: Virtual environment (not tracked in git)

## Architecture

### High-Level Architecture

The Strands Agents SDK follows a modular architecture designed around a central agent loop that coordinates interactions between models, tools, and conversation management. The architecture is designed to be flexible, extensible, and model-agnostic.

```
┌─────────────────────────────────────────────────────────────┐
│                         Agent                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌───────────────┐    ┌───────────────┐    ┌───────────────┐│
│  │ Event Loop    │◄───┤ Model Provider│◄───┤ Tools         ││
│  └───────┬───────┘    └───────────────┘    └───────────────┘│
│          │                                                  │
│  ┌───────▼───────┐    ┌───────────────┐    ┌───────────────┐│
│  │ Conversation  │    │ Handlers      │    │ Telemetry     ││
│  │ Management    │    │               │    │               ││
│  └───────────────┘    └───────────────┘    └───────────────┘│
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Core Components

- **Agent**: The central component that orchestrates interactions between models, tools, and conversation management
- **Event Loop**: Manages the flow of messages between the agent, model, and tools
- **Model Providers**: Abstractions for different LLM providers
- **Tools**: Utilities that extend the agent's capabilities
- **Conversation Management**: Handles the storage, retrieval, and management of conversation history
- **Handlers**: Components that process events during the agent's operation
- **Telemetry**: Provides metrics, tracing, and logging capabilities

### Key Design Principles

1. **Modularity**: Components are designed to be interchangeable and extensible
2. **Model Agnosticism**: Support for multiple model providers with a consistent interface
3. **Simplicity**: Simple API for basic use cases with the ability to customize for complex scenarios
4. **Extensibility**: Easy to add new tools, models, and capabilities
5. **Observability**: Built-in telemetry for monitoring and debugging

### Communication Flow

1. User sends a message to the agent
2. Agent processes the message through the event loop
3. Model generates a response or tool invocation
4. If a tool is invoked, the tool handler executes it and returns the result
5. Results are sent back to the model for further processing
6. Final response is returned to the user

## Components

### Agent Module

- **agent.py**: Main Agent class implementation
- **agent_result.py**: Represents the result of an agent operation
- **conversation_manager/**: Manages conversation history
  - **conversation_manager.py**: Base conversation manager interface
  - **file_conversation_manager.py**: Stores conversations in files
  - **null_conversation_manager.py**: No-op conversation manager
  - **sliding_window_conversation_manager.py**: Maintains a sliding window of messages
  - **summarizing_conversation_manager.py**: Summarizes conversation history

### Event Loop Module

- **event_loop.py**: Core event loop implementation
- **error_handler.py**: Handles errors during event loop execution
- **message_processor.py**: Processes messages in the event loop
- **streaming.py**: Handles streaming responses

### Handlers Module

- **callback_handler.py**: Callback system for monitoring agent operations
- **tool_handler.py**: Handles tool invocations

### Models Module

- **bedrock.py**: Amazon Bedrock model provider
- **anthropic.py**: Anthropic model provider
- **litellm.py**: LiteLLM model provider
- **llamaapi.py**: LlamaAPI model provider
- **ollama.py**: Ollama model provider
- **openai.py**: OpenAI model provider

### Tools Module

- **tools.py**: Core tools implementation
- **registry.py**: Tool registration system
- **mcp/**: Model Context Protocol integration
  - **mcp_agent_tool.py**: MCP tool implementation
  - **mcp_client.py**: Client for MCP servers
  - **mcp_types.py**: Type definitions for MCP

### Types Module

- **content.py**: Content type definitions
- **event_loop.py**: Event loop type definitions
- **exceptions.py**: Exception definitions
- **guardrails.py**: Guardrail type definitions
- **media.py**: Media type definitions
- **models/**: Model type definitions
  - **model.py**: Base model interface
  - **openai.py**: OpenAI-specific types
- **streaming.py**: Streaming type definitions
- **tools.py**: Tool type definitions
- **traces.py**: Tracing type definitions

### Telemetry Module

- Provides metrics, tracing, and logging capabilities

## Interfaces

### Agent Interface

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

```python
class ConversationManager:
    def add_user_message(self, content: str) -> None: ...
    
    def add_assistant_message(self, content: str) -> None: ...
    
    def get_messages(self) -> List[Message]: ...
    
    def clear(self) -> None: ...
```

### Callback Handler Interface

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

## Data Models

### Core Data Models

#### Message

```python
class Message:
    role: str  # "user", "assistant", "system", "tool"
    content: Union[str, List[ContentItem]]
    name: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None
    tool_call_id: Optional[str] = None
```

#### ContentItem

```python
class ContentItem:
    type: str  # "text", "image", etc.
    text: Optional[str] = None
    image_url: Optional[ImageUrl] = None
```

#### ToolCall

```python
class ToolCall:
    id: str
    name: str
    arguments: Dict[str, Any]
```

#### ModelResponse

```python
class ModelResponse:
    content: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None
    stop_reason: Optional[str] = None
```

#### AgentResult

```python
class AgentResult:
    content: str
    tool_calls: List[Dict[str, Any]]
    raw_response: Any
```

## Workflows

### Basic Agent Interaction

```python
from strands import Agent
from strands_tools import calculator

# Create agent with calculator tool
agent = Agent(tools=[calculator])

# Send message and get response
response = agent("What is the square root of 1764?")

# Print response
print(response)
```

### Streaming Interaction

```python
from strands import Agent

# Create agent
agent = Agent()

# Stream response
for chunk in agent.stream("Tell me about AI agents"):
    print(chunk, end="", flush=True)
```

### Asynchronous Interaction

```python
import asyncio
from strands import Agent

async def main():
    agent = Agent()
    response = await agent.acall("What is the weather today?")
    print(response)

    async for chunk in agent.astream("Tell me about AI agents"):
        print(chunk, end="", flush=True)

asyncio.run(main())
```

### Tool Registration and Usage

```python
from strands import Agent, tool

@tool
def word_count(text: str) -> int:
    """Count words in text."""
    return len(text.split())

agent = Agent(tools=[word_count])
response = agent("How many words are in this sentence?")
```

### MCP Integration

```python
from strands import Agent
from strands.tools.mcp import MCPClient
from mcp import stdio_client, StdioServerParameters

# Create MCP client
aws_docs_client = MCPClient(
    lambda: stdio_client(StdioServerParameters(command="uvx", args=["awslabs.aws-documentation-mcp-server@latest"]))
)

# Use MCP client in a context manager
with aws_docs_client:
    # List available tools
    tools = aws_docs_client.list_tools_sync()
    
    # Create agent with MCP tools
    agent = Agent(tools=tools)
    
    # Use agent with MCP tools
    response = agent("Tell me about Amazon Bedrock")
```

## Dependencies

### Required Dependencies

- boto3 (>=1.26.0,<2.0.0)
- botocore (>=1.29.0,<2.0.0)
- docstring_parser (>=0.15,<0.16.0)
- mcp (>=1.8.0,<2.0.0)
- pydantic (>=2.0.0,<3.0.0)
- typing-extensions (>=4.13.2,<5.0.0)
- watchdog (>=6.0.0,<7.0.0)
- opentelemetry-api (>=1.30.0,<2.0.0)
- opentelemetry-sdk (>=1.30.0,<2.0.0)

### Optional Dependencies

- anthropic (>=0.21.0,<1.0.0)
- litellm (>=1.69.0,<2.0.0)
- llama-api-client (>=0.1.0,<1.0.0)
- ollama (>=0.4.8,<1.0.0)
- openai (>=1.68.0,<2.0.0)

### Python Version Compatibility

- Python 3.10
- Python 3.11
- Python 3.12
- Python 3.13

## Codebase Overview

### Directory Structure

```
src/strands/
├── agent/
│   ├── conversation_manager/
│   ├── agent.py
│   ├── agent_result.py
│   └── __init__.py
├── event_loop/
├── handlers/
├── models/
├── telemetry/
├── tools/
│   ├── mcp/
├── types/
│   ├── models/
└── __init__.py
```

### Code Organization Patterns

- **Interface-Implementation Pattern**: Clear contracts between components
- **Decorator Pattern**: Simplifies tool definition
- **Factory Pattern**: Creates instances of various components
- **Composition Pattern**: Combines multiple components
- **Observer Pattern**: Used for callbacks

### Testing Structure

```
tests/
├── strands/
│   ├── agent/
│   ├── event_loop/
│   ├── handlers/
│   ├── models/
│   ├── tools/
│   └── types/
└── conftest.py
```

Tests use pytest and pytest-asyncio for testing both synchronous and asynchronous code.
