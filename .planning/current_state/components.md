# Strands Agents Components

## Core Components

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

## Component Relationships

- **Agent** uses **Event Loop** to process messages
- **Agent** uses **Model Providers** to generate responses
- **Agent** uses **Tools** to extend capabilities
- **Agent** uses **Conversation Manager** to maintain history
- **Event Loop** uses **Handlers** to process events
- **Tools** can be extended via **MCP** integration
- **Telemetry** is used throughout for monitoring

## Component Responsibilities

### Agent
- Provides the main interface for users
- Coordinates interactions between components
- Manages conversation state

### Event Loop
- Processes messages between agent, model, and tools
- Handles streaming responses
- Manages error handling

### Model Providers
- Abstract communication with LLM providers
- Handle model-specific parameters and formats
- Process responses from models

### Tools
- Extend agent capabilities
- Execute specific tasks
- Provide results back to the agent

### Conversation Management
- Stores conversation history
- Manages context window limitations
- Provides summarization capabilities

### Handlers
- Process events during agent operation
- Execute tool invocations
- Provide callback mechanisms

### Telemetry
- Collects metrics on agent operations
- Provides tracing for debugging
- Logs important events
