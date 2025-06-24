# Strands Agents Workflows

## Core Workflows

### Basic Agent Interaction

The most common workflow for interacting with an agent:

1. Create an agent instance with desired model and tools
2. Send a message to the agent
3. Agent processes the message through the event loop
4. Model generates a response or tool invocation
5. If a tool is invoked, the tool handler executes it and returns the result
6. Results are sent back to the model for further processing
7. Final response is returned to the user

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

For use cases where you want to receive partial responses as they're generated:

1. Create an agent instance
2. Call the stream method with a message
3. Process each chunk of the response as it arrives

```python
from strands import Agent

# Create agent
agent = Agent()

# Stream response
for chunk in agent.stream("Tell me about AI agents"):
    print(chunk, end="", flush=True)
```

### Asynchronous Interaction

For use cases where you want to use the agent in an asynchronous context:

1. Create an agent instance
2. Use acall or astream methods in an async context
3. Process the response asynchronously

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

For extending agent capabilities with custom tools:

1. Define a tool using the @tool decorator
2. Create an agent instance with the tool
3. Use the agent with the tool

```python
from strands import Agent, tool

@tool
def word_count(text: str) -> int:
    """Count words in text."""
    return len(text.split())

agent = Agent(tools=[word_count])
response = agent("How many words are in this sentence?")
```

### Direct Tool Access

For programmatically accessing tools:

1. Create an agent instance with tools
2. Access tools directly using the agent.tool namespace

```python
from strands import Agent, tool

@tool
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b

agent = Agent(tools=[add])
result = agent.tool.add(a=5, b=3)
print(result)  # 8
```

### MCP Integration

For integrating with Model Context Protocol servers:

1. Create an MCP client
2. Connect to the MCP server
3. List available tools
4. Create an agent with the MCP tools
5. Use the agent with the MCP tools

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

### Conversation Management

For managing conversation history:

1. Create a conversation manager
2. Create an agent with the conversation manager
3. Interact with the agent, which will maintain conversation history

```python
from strands import Agent
from strands.agent.conversation_manager import SlidingWindowConversationManager

# Create conversation manager with a window size of 10 messages
conversation_manager = SlidingWindowConversationManager(window_size=10)

# Create agent with conversation manager
agent = Agent(conversation_manager=conversation_manager)

# Interact with the agent
agent("Hello, who are you?")
agent("What can you help me with?")
```

### Custom Model Provider

For using a custom model provider:

1. Create a custom model provider class
2. Create an agent with the custom model provider
3. Use the agent with the custom model provider

```python
from strands import Agent
from strands.types.models import Model, ModelResponse

class CustomModel(Model):
    async def generate(self, messages, tools=None, **kwargs):
        # Custom implementation
        return ModelResponse(content="Custom response")
    
    async def generate_stream(self, messages, tools=None, **kwargs):
        # Custom implementation
        yield ModelResponseChunk(content="Custom", is_finished=False)
        yield ModelResponseChunk(content=" response", is_finished=True)

# Create agent with custom model
agent = Agent(model=CustomModel())

# Use agent
response = agent("Hello")
```

### Callback Handling

For monitoring and customizing agent behavior:

1. Create a custom callback handler
2. Create an agent with the callback handler
3. Use the agent, which will trigger callbacks

```python
from strands import Agent
from strands.handlers.callback_handler import CallbackHandler

class CustomCallbackHandler(CallbackHandler):
    def on_llm_start(self, model, prompt):
        print(f"Starting LLM call to {model}")
    
    def on_llm_end(self, model, response):
        print(f"LLM call to {model} completed")
    
    def on_tool_start(self, tool_name, tool_input):
        print(f"Starting tool call to {tool_name}")
    
    def on_tool_end(self, tool_name, tool_output):
        print(f"Tool call to {tool_name} completed")

# Create agent with custom callback handler
agent = Agent(callback_handler=CustomCallbackHandler())

# Use agent
response = agent("Hello")
```
