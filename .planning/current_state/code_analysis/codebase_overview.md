# Strands Agents Codebase Overview

## Directory Structure

```
src/strands/
├── agent/
│   ├── conversation_manager/
│   │   ├── conversation_manager.py
│   │   ├── file_conversation_manager.py
│   │   ├── __init__.py
│   │   ├── null_conversation_manager.py
│   │   ├── sliding_window_conversation_manager.py
│   │   └── summarizing_conversation_manager.py
│   ├── agent.py
│   ├── agent_result.py
│   └── __init__.py
├── event_loop/
│   ├── error_handler.py
│   ├── event_loop.py
│   ├── __init__.py
│   ├── message_processor.py
│   └── streaming.py
├── handlers/
│   ├── callback_handler.py
│   ├── __init__.py
│   └── tool_handler.py
├── models/
│   ├── anthropic.py
│   ├── bedrock.py
│   ├── __init__.py
│   ├── litellm.py
│   ├── llamaapi.py
│   ├── ollama.py
│   └── openai.py
├── telemetry/
│   ├── __init__.py
│   ├── metrics.py
│   └── tracer.py
├── tools/
│   ├── mcp/
│   │   ├── __init__.py
│   │   ├── mcp_agent_tool.py
│   │   ├── mcp_client.py
│   │   └── mcp_types.py
│   ├── __init__.py
│   ├── registry.py
│   ├── thread_pool_executor.py
│   ├── tools.py
│   └── watcher.py
├── types/
│   ├── models/
│   │   ├── __init__.py
│   │   ├── model.py
│   │   └── openai.py
│   ├── content.py
│   ├── event_loop.py
│   ├── exceptions.py
│   ├── guardrails.py
│   ├── __init__.py
│   ├── media.py
│   ├── streaming.py
│   ├── tools.py
│   └── traces.py
└── __init__.py
```

## Key Components

### Agent Module

The agent module is the core of the SDK, providing the main interface for users to interact with foundation models and tools. It includes:

- **agent.py**: Implements the Agent class, which serves as the primary entry point for the SDK
- **agent_result.py**: Defines the AgentResult class, which represents the result of an agent operation
- **conversation_manager/**: Contains classes for managing conversation history

The Agent class supports both natural language interaction (`agent("Hello")`) and method-style tool access (`agent.tool.add(a=1, b=2)`).

### Event Loop Module

The event loop module manages the flow of messages between the agent, model, and tools. It includes:

- **event_loop.py**: Implements the core event loop logic
- **error_handler.py**: Handles errors during event loop execution
- **message_processor.py**: Processes messages in the event loop
- **streaming.py**: Handles streaming responses

The event loop is responsible for processing model responses, executing tool calls, and managing the conversation flow.

### Handlers Module

The handlers module provides components for processing events during agent operation:

- **callback_handler.py**: Implements the callback system for monitoring agent operations
- **tool_handler.py**: Handles tool invocations

Handlers can be customized to extend or modify the behavior of the agent.

### Models Module

The models module provides abstractions for different LLM providers:

- **bedrock.py**: Amazon Bedrock model provider
- **anthropic.py**: Anthropic model provider
- **litellm.py**: LiteLLM model provider
- **llamaapi.py**: LlamaAPI model provider
- **ollama.py**: Ollama model provider
- **openai.py**: OpenAI model provider

Each model provider implements the Model interface defined in types/models/model.py.

### Tools Module

The tools module provides utilities for extending agent capabilities:

- **tools.py**: Implements the core tools functionality
- **registry.py**: Manages tool registration
- **mcp/**: Provides integration with Model Context Protocol servers

Tools can be defined using the @tool decorator and registered with the agent.

### Types Module

The types module defines the data structures used throughout the SDK:

- **content.py**: Content type definitions
- **event_loop.py**: Event loop type definitions
- **exceptions.py**: Exception definitions
- **guardrails.py**: Guardrail type definitions
- **media.py**: Media type definitions
- **models/**: Model type definitions
- **streaming.py**: Streaming type definitions
- **tools.py**: Tool type definitions
- **traces.py**: Tracing type definitions

### Telemetry Module

The telemetry module provides metrics, tracing, and logging capabilities:

- **metrics.py**: Implements metrics collection
- **tracer.py**: Implements distributed tracing

## Code Organization Patterns

### Interface-Implementation Pattern

The SDK uses the interface-implementation pattern to define clear contracts between components:

- **Model** interface with multiple implementations (BedrockModel, AnthropicModel, etc.)
- **ConversationManager** interface with multiple implementations (SlidingWindowConversationManager, SummarizingConversationManager, etc.)
- **CallbackHandler** interface with multiple implementations (PrintingCallbackHandler, CompositeCallbackHandler, etc.)

### Decorator Pattern

The SDK uses decorators to simplify tool definition:

```python
@tool
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b
```

### Factory Pattern

The SDK uses factory methods to create instances of various components:

- **Model.from_config()**: Creates a model instance from a configuration
- **ConversationManager.from_config()**: Creates a conversation manager instance from a configuration

### Composition Pattern

The SDK uses composition to combine multiple components:

- **CompositeCallbackHandler**: Combines multiple callback handlers
- **Agent**: Composes model, tools, conversation manager, and handlers

### Observer Pattern

The SDK uses the observer pattern for callbacks:

- **CallbackHandler**: Observes events during agent operation
- **Agent**: Notifies observers of events

## Testing Structure

The SDK has a comprehensive test suite organized in a similar structure to the source code:

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

## Integration Tests

Integration tests are separated from unit tests:

```
tests-integ/
└── strands/
    ├── models/
    └── tools/
```

These tests interact with external services and require appropriate credentials.
