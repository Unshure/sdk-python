# Strands Agents SDK Workspace Information

## Overview
This workspace contains the Strands Agents Python SDK, a model-driven approach to building AI agents in just a few lines of code. The SDK provides a simple yet powerful framework for creating AI agents that can interact with various model providers and tools.

## Repository Structure
- **src/strands**: Main source code directory
- **tests**: Unit tests
- **tests-integ**: Integration tests
- **tools**: Development tools
- **build**: Build artifacts
- **.github**: GitHub workflows and configuration
- **.venv**: Virtual environment (not tracked in git)

## Key Features
- Lightweight & flexible agent loop
- Model agnostic (supports Amazon Bedrock, Anthropic, LiteLLM, Llama, Ollama, OpenAI)
- Advanced capabilities including multi-agent systems and streaming support
- Built-in MCP (Model Context Protocol) support

## Dependencies
- Python 3.10+
- boto3/botocore
- docstring_parser
- mcp
- pydantic
- typing-extensions
- watchdog
- opentelemetry-api/sdk
- Optional dependencies for specific model providers (anthropic, litellm, llamaapi, ollama, openai)

## Development Tools
- commitizen
- hatch
- mypy
- pre-commit
- pytest
- ruff

## License
Apache License 2.0
