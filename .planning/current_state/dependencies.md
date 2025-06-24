# Strands Agents Dependencies

## Core Dependencies

### Required Dependencies

| Dependency | Version | Purpose |
|------------|---------|---------|
| boto3 | >=1.26.0,<2.0.0 | AWS SDK for Python, used for Amazon Bedrock integration |
| botocore | >=1.29.0,<2.0.0 | Low-level AWS API client, used by boto3 |
| docstring_parser | >=0.15,<0.16.0 | Parses Python docstrings for tool documentation |
| mcp | >=1.8.0,<2.0.0 | Model Context Protocol implementation |
| pydantic | >=2.0.0,<3.0.0 | Data validation and settings management |
| typing-extensions | >=4.13.2,<5.0.0 | Backported typing features |
| watchdog | >=6.0.0,<7.0.0 | File system monitoring |
| opentelemetry-api | >=1.30.0,<2.0.0 | Telemetry API |
| opentelemetry-sdk | >=1.30.0,<2.0.0 | Telemetry SDK |

### Optional Dependencies

#### Model Provider Dependencies

| Dependency | Version | Purpose |
|------------|---------|---------|
| anthropic | >=0.21.0,<1.0.0 | Anthropic Claude model integration |
| litellm | >=1.69.0,<2.0.0 | Unified interface for multiple LLM providers |
| llama-api-client | >=0.1.0,<1.0.0 | Llama API integration |
| ollama | >=0.4.8,<1.0.0 | Ollama model integration |
| openai | >=1.68.0,<2.0.0 | OpenAI model integration |

#### Development Dependencies

| Dependency | Version | Purpose |
|------------|---------|---------|
| commitizen | >=4.4.0,<5.0.0 | Standardized commit messages |
| hatch | >=1.0.0,<2.0.0 | Build tool |
| moto | >=5.1.0,<6.0.0 | AWS service mocking |
| mypy | >=1.15.0,<2.0.0 | Static type checking |
| pre-commit | >=3.2.0,<4.2.0 | Git hooks |
| pytest | >=8.0.0,<9.0.0 | Testing framework |
| pytest-asyncio | >=0.26.0,<0.27.0 | Async testing support |
| ruff | >=0.4.4,<0.5.0 | Fast Python linter |
| swagger-parser | >=1.0.2,<2.0.0 | Swagger/OpenAPI parsing |

#### Documentation Dependencies

| Dependency | Version | Purpose |
|------------|---------|---------|
| sphinx | >=5.0.0,<6.0.0 | Documentation generator |
| sphinx-rtd-theme | >=1.0.0,<2.0.0 | Read the Docs theme |
| sphinx-autodoc-typehints | >=1.12.0,<2.0.0 | Type hints in documentation |

#### Telemetry Dependencies

| Dependency | Version | Purpose |
|------------|---------|---------|
| opentelemetry-exporter-otlp-proto-http | >=1.30.0,<2.0.0 | OpenTelemetry HTTP exporter |

#### A2A Dependencies

| Dependency | Version | Purpose |
|------------|---------|---------|
| a2a-sdk | >=0.2.6 | Agent-to-Agent SDK |
| uvicorn | >=0.34.2 | ASGI server |
| httpx | >=0.28.1 | HTTP client |
| fastapi | >=0.115.12 | Web framework |
| starlette | >=0.46.2 | ASGI framework |

## External Dependencies

### AWS Services

- **Amazon Bedrock**: Used for accessing foundation models
- **AWS IAM**: Used for authentication and authorization

### Third-Party Services

- **Anthropic API**: Used for accessing Claude models
- **OpenAI API**: Used for accessing GPT models
- **Llama API**: Used for accessing Llama models

## Internal Dependencies

### Module Dependencies

| Module | Depends On |
|--------|------------|
| agent | event_loop, handlers, models, tools, telemetry |
| event_loop | handlers, telemetry |
| handlers | tools |
| models | types |
| tools | types |
| telemetry | - |
| types | - |

### Class Dependencies

| Class | Depends On |
|-------|------------|
| Agent | Model, ToolRegistry, ConversationManager, CallbackHandler, ToolHandler |
| EventLoop | Model, ToolHandler, CallbackHandler |
| Model | - |
| ToolRegistry | - |
| ConversationManager | - |
| CallbackHandler | - |
| ToolHandler | - |
| MCPClient | - |

## Python Version Compatibility

- Python 3.10
- Python 3.11
- Python 3.12
- Python 3.13
