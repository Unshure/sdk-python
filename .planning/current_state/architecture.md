# Strands Agents Architecture

## High-Level Architecture

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

## Core Components

### Agent
The central component that orchestrates interactions between models, tools, and conversation management. It provides both natural language and method-style interfaces for interacting with the system.

### Event Loop
Manages the flow of messages between the agent, model, and tools. It handles the processing of model responses, tool invocations, and streaming.

### Model Providers
Abstractions for different LLM providers (Bedrock, Anthropic, OpenAI, etc.) that handle the communication with the underlying models.

### Tools
Utilities that extend the agent's capabilities, allowing it to perform specific tasks. Tools can be Python functions, classes, or MCP-based tools.

### Conversation Management
Handles the storage, retrieval, and management of conversation history, including summarization and sliding window approaches.

### Handlers
Components that process events during the agent's operation, such as callback handlers for monitoring and tool handlers for executing tools.

### Telemetry
Provides metrics, tracing, and logging capabilities for monitoring and debugging agent operations.

## Key Design Principles

1. **Modularity**: Components are designed to be interchangeable and extensible.
2. **Model Agnosticism**: Support for multiple model providers with a consistent interface.
3. **Simplicity**: Simple API for basic use cases with the ability to customize for complex scenarios.
4. **Extensibility**: Easy to add new tools, models, and capabilities.
5. **Observability**: Built-in telemetry for monitoring and debugging.

## Communication Flow

1. User sends a message to the agent
2. Agent processes the message through the event loop
3. Model generates a response or tool invocation
4. If a tool is invoked, the tool handler executes it and returns the result
5. Results are sent back to the model for further processing
6. Final response is returned to the user

## Integration Points

- **MCP Support**: Integration with Model Context Protocol servers for accessing external tools
- **Custom Model Providers**: Ability to implement custom model providers
- **Tool Registration**: Flexible tool registration system for extending agent capabilities
- **Callback System**: Extensible callback system for monitoring and customizing agent behavior
