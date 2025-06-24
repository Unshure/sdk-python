# Strands Agents SDK Knowledge Base

## Overview

This knowledge base contains comprehensive documentation about the Strands Agents Python SDK, a model-driven approach to building AI agents. The documentation covers the architecture, components, interfaces, data models, workflows, and dependencies of the SDK.

Last Updated: 2025-06-18

## How to Use This Knowledge Base

This index file serves as a guide to the documentation contained in this knowledge base. Each file focuses on a specific aspect of the SDK, and this index provides a summary of each file's content to help you find the information you need.

When asking questions about the Strands Agents SDK, Amazon Q will use this knowledge base to provide accurate and detailed answers. You can ask questions about:

- The overall architecture and design of the SDK
- Specific components and their responsibilities
- How to implement various workflows
- The interfaces and data models used in the SDK
- Dependencies and requirements

## Documentation Files

### [workspace_info.md](workspace_info.md)
- Basic information about the workspace
- Repository structure
- Key features
- Dependencies
- Development tools
- License information

### [architecture.md](architecture.md)
- High-level architecture diagram
- Core components overview
- Key design principles
- Communication flow
- Integration points

### [components.md](components.md)
- Detailed description of each component
- Component relationships
- Component responsibilities
- Module organization

### [interfaces.md](interfaces.md)
- Core interfaces (Agent, Model, Tool, etc.)
- Message formats
- Event loop types
- Tool types

### [data_models.md](data_models.md)
- Core data models (Message, ContentItem, ToolCall, etc.)
- Model provider data models
- Tool data models
- Telemetry data models

### [workflows.md](workflows.md)
- Basic agent interaction
- Streaming interaction
- Asynchronous interaction
- Tool registration and usage
- Direct tool access
- MCP integration
- Conversation management
- Custom model provider
- Callback handling

### [dependencies.md](dependencies.md)
- Core dependencies
- Optional dependencies
- External dependencies
- Internal dependencies
- Python version compatibility

### [code_analysis/codebase_overview.md](code_analysis/codebase_overview.md)
- Directory structure
- Key components
- Code organization patterns
- Testing structure
- Integration tests

## Common Questions and Where to Find Answers

1. **"What is Strands Agents?"**
   - See [workspace_info.md](workspace_info.md) for a high-level overview

2. **"How does the agent architecture work?"**
   - See [architecture.md](architecture.md) for the high-level architecture
   - See [components.md](components.md) for detailed component descriptions

3. **"How do I create a custom tool?"**
   - See [workflows.md](workflows.md) for examples of tool registration and usage

4. **"What model providers are supported?"**
   - See [dependencies.md](dependencies.md) for a list of supported model providers
   - See [components.md](components.md) for details on the models module

5. **"How does conversation management work?"**
   - See [components.md](components.md) for details on the conversation manager
   - See [workflows.md](workflows.md) for examples of conversation management

6. **"How do I use streaming responses?"**
   - See [workflows.md](workflows.md) for examples of streaming interaction

7. **"What is MCP and how do I use it?"**
   - See [components.md](components.md) for details on the MCP integration
   - See [workflows.md](workflows.md) for examples of MCP usage

8. **"How do I customize agent behavior?"**
   - See [workflows.md](workflows.md) for examples of callback handling
   - See [interfaces.md](interfaces.md) for details on the callback handler interface

9. **"What are the core data structures used in the SDK?"**
   - See [data_models.md](data_models.md) for details on the core data models

10. **"How is the codebase organized?"**
    - See [code_analysis/codebase_overview.md](code_analysis/codebase_overview.md) for details on the codebase organization
