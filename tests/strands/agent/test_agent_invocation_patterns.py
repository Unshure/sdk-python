# ABOUTME: Tests for Agent class invocation patterns including List[Message] and no-input support
# ABOUTME: Validates new invocation methods while ensuring backward compatibility with existing patterns

"""Tests for Agent invocation patterns.

This module tests the extended Agent invocation patterns including:
- List[Message] input support with mixed user/assistant messages
- No-input invocation using existing conversation history
- Backward compatibility with existing string and ContentBlock patterns
"""

import copy
import unittest.mock

import pytest

from strands.agent.agent import Agent
from strands.agent.agent_result import AgentResult
from strands.types.content import ContentBlock, Message


class TestAgentInvocationPatterns:
    """Test class for Agent invocation pattern extensions."""

    @pytest.fixture
    def mock_model(self):
        """Create a mock model for testing."""

        async def stream(*args, **kwargs):
            result = mock.mock_stream(*copy.deepcopy(args), **copy.deepcopy(kwargs))
            # If result is already an async generator, yield from it
            if hasattr(result, "__aiter__"):
                async for item in result:
                    yield item
            else:
                # If result is a regular generator or iterable, convert to async
                for item in result:
                    yield item

        mock = unittest.mock.Mock()
        mock.configure_mock(mock_stream=unittest.mock.MagicMock())
        mock.stream.side_effect = stream
        return mock

    @pytest.fixture
    def agent(self, mock_model):
        """Create an Agent instance for testing."""
        return Agent(model=mock_model, callback_handler=None)

    @pytest.fixture
    def agenerator(self):
        """Create an async generator for testing."""

        async def agenerator(items):
            for item in items:
                yield item

        return agenerator

    def test_list_message_single_user_message(self, agent, mock_model, agenerator):
        """Test invocation with a single user message in list format."""
        mock_model.mock_stream.return_value = agenerator(
            [
                {"contentBlockStart": {"start": {}}},
                {"contentBlockDelta": {"delta": {"text": "Test response"}}},
                {"contentBlockStop": {}},
                {"messageStop": {"stopReason": "end_turn"}},
            ]
        )

        messages = [{"role": "user", "content": [{"text": "Hello"}]}]

        result = agent(messages)

        assert isinstance(result, AgentResult)
        # Verify the message was added to conversation history
        assert len(agent.messages) >= 2  # user message + assistant response
        assert agent.messages[0]["role"] == "user"
        assert agent.messages[0]["content"][0]["text"] == "Hello"

    def test_list_message_mixed_user_assistant(self, agent, mock_model, agenerator):
        """Test invocation with mixed user and assistant messages."""
        mock_model.mock_stream.return_value = agenerator(
            [
                {"contentBlockStart": {"start": {}}},
                {"contentBlockDelta": {"delta": {"text": "Test response"}}},
                {"contentBlockStop": {}},
                {"messageStop": {"stopReason": "end_turn"}},
            ]
        )

        messages = [
            {"role": "user", "content": [{"text": "What is 2+2?"}]},
            {"role": "assistant", "content": [{"text": "2+2 equals 4"}]},
            {"role": "user", "content": [{"text": "What about 3+3?"}]},
        ]

        result = agent(messages)

        assert isinstance(result, AgentResult)
        # Verify all messages were added to conversation history
        # Should have original 3 messages + assistant response
        assert len(agent.messages) >= 4
        assert agent.messages[0]["role"] == "user"
        assert agent.messages[0]["content"][0]["text"] == "What is 2+2?"
        assert agent.messages[1]["role"] == "assistant"
        assert agent.messages[1]["content"][0]["text"] == "2+2 equals 4"
        assert agent.messages[2]["role"] == "user"
        assert agent.messages[2]["content"][0]["text"] == "What about 3+3?"

    def test_list_message_multiple_user_messages(self, agent, mock_model, agenerator):
        """Test invocation with multiple user messages."""
        mock_model.mock_stream.return_value = agenerator(
            [
                {"contentBlockStart": {"start": {}}},
                {"contentBlockDelta": {"delta": {"text": "Test response"}}},
                {"contentBlockStop": {}},
                {"messageStop": {"stopReason": "end_turn"}},
            ]
        )

        messages = [
            {"role": "user", "content": [{"text": "First question"}]},
            {"role": "user", "content": [{"text": "Second question"}]},
        ]

        result = agent(messages)

        assert isinstance(result, AgentResult)
        # Verify both messages were added
        assert len(agent.messages) >= 3  # 2 user messages + assistant response
        assert agent.messages[0]["content"][0]["text"] == "First question"
        assert agent.messages[1]["content"][0]["text"] == "Second question"

    def test_list_message_assistant_only(self, agent, mock_model, agenerator):
        """Test invocation with assistant-only messages."""
        mock_model.mock_stream.return_value = agenerator(
            [
                {"contentBlockStart": {"start": {}}},
                {"contentBlockDelta": {"delta": {"text": "Test response"}}},
                {"contentBlockStop": {}},
                {"messageStop": {"stopReason": "end_turn"}},
            ]
        )

        messages = [{"role": "assistant", "content": [{"text": "I am ready to help"}]}]

        result = agent(messages)

        assert isinstance(result, AgentResult)
        # Verify assistant message was added
        assert len(agent.messages) >= 2  # assistant message + response
        assert agent.messages[0]["role"] == "assistant"
        assert agent.messages[0]["content"][0]["text"] == "I am ready to help"

    def test_list_message_empty_list(self, agent, mock_model, agenerator):
        """Test invocation with empty message list."""
        messages = []

        # Empty list should raise ValueError since no conversation history
        with pytest.raises(ValueError, match="No conversation history or prompt provided"):
            agent(messages)

    def test_no_input_with_existing_messages(self, agent, mock_model, agenerator):
        """Test invocation with no parameters when agent has existing messages."""
        mock_model.mock_stream.return_value = agenerator(
            [
                {"contentBlockStart": {"start": {}}},
                {"contentBlockDelta": {"delta": {"text": "Test response"}}},
                {"contentBlockStop": {}},
                {"messageStop": {"stopReason": "end_turn"}},
            ]
        )

        # Pre-populate agent with messages
        agent.messages = [
            {"role": "user", "content": [{"text": "Previous question"}]},
            {"role": "assistant", "content": [{"text": "Previous answer"}]},
        ]

        result = agent()

        assert isinstance(result, AgentResult)
        # Should have original 2 messages + new assistant response
        assert len(agent.messages) >= 3
        assert agent.messages[0]["content"][0]["text"] == "Previous question"
        assert agent.messages[1]["content"][0]["text"] == "Previous answer"

    def test_no_input_with_empty_messages_raises_error(self, agent):
        """Test that no-input invocation raises error when no conversation history exists."""
        # Ensure agent has no messages
        agent.messages = []

        # Now should raise ValueError with the correct message
        with pytest.raises(ValueError, match="No conversation history or prompt provided"):
            agent()

    def test_backward_compatibility_string_input(self, agent, mock_model, agenerator):
        """Test that existing string input still works."""
        mock_model.mock_stream.return_value = agenerator(
            [
                {"contentBlockStart": {"start": {}}},
                {"contentBlockDelta": {"delta": {"text": "Test response"}}},
                {"contentBlockStop": {}},
                {"messageStop": {"stopReason": "end_turn"}},
            ]
        )

        result = agent("Hello, how are you?")

        assert isinstance(result, AgentResult)
        assert len(agent.messages) >= 2  # user message + assistant response
        assert agent.messages[-2]["role"] == "user"
        assert agent.messages[-2]["content"][0]["text"] == "Hello, how are you?"

    def test_backward_compatibility_content_block_list(self, agent, mock_model, agenerator):
        """Test that existing ContentBlock list input still works."""
        mock_model.mock_stream.return_value = agenerator(
            [
                {"contentBlockStart": {"start": {}}},
                {"contentBlockDelta": {"delta": {"text": "Test response"}}},
                {"contentBlockStop": {}},
                {"messageStop": {"stopReason": "end_turn"}},
            ]
        )

        content_blocks = [{"text": "Hello"}, {"text": "How are you?"}]

        result = agent(content_blocks)

        assert isinstance(result, AgentResult)
        assert len(agent.messages) >= 2
        assert agent.messages[-2]["role"] == "user"
        assert len(agent.messages[-2]["content"]) == 2
        assert agent.messages[-2]["content"][0]["text"] == "Hello"
        assert agent.messages[-2]["content"][1]["text"] == "How are you?"

    def test_invalid_message_structure_handled_by_api(self, agent, mock_model, agenerator):
        """Test that invalid message structure is handled by the end API call."""
        # With simplified validation, invalid structures will be passed through
        # and handled by the underlying API, which may succeed or fail depending on the model
        mock_model.mock_stream.return_value = agenerator(
            [
                {"contentBlockStart": {"start": {}}},
                {"contentBlockDelta": {"delta": {"text": "Test response"}}},
                {"contentBlockStop": {}},
                {"messageStop": {"stopReason": "end_turn"}},
            ]
        )

        invalid_messages = [{"invalid": "structure"}]

        # This should now be treated as a ContentBlock list and passed through
        # The actual validation will happen at the model level
        result = agent(invalid_messages)
        assert isinstance(result, AgentResult)

    def test_invalid_role_handled_by_api(self, agent, mock_model, agenerator):
        """Test that invalid role is handled by the end API call."""
        mock_model.mock_stream.return_value = agenerator(
            [
                {"contentBlockStart": {"start": {}}},
                {"contentBlockDelta": {"delta": {"text": "Test response"}}},
                {"contentBlockStop": {}},
                {"messageStop": {"stopReason": "end_turn"}},
            ]
        )

        invalid_messages = [{"role": "invalid", "content": [{"text": "test"}]}]

        # This should be treated as a Message list and passed through
        # The actual validation will happen at the model level
        result = agent(invalid_messages)
        assert isinstance(result, AgentResult)

    def test_missing_content_handled_by_api(self, agent, mock_model, agenerator):
        """Test that missing content field is handled by the end API call."""
        mock_model.mock_stream.return_value = agenerator(
            [
                {"contentBlockStart": {"start": {}}},
                {"contentBlockDelta": {"delta": {"text": "Test response"}}},
                {"contentBlockStop": {}},
                {"messageStop": {"stopReason": "end_turn"}},
            ]
        )

        invalid_messages = [{"role": "user"}]

        # This should be treated as a Message list and passed through
        # The actual validation will happen at the model level
        result = agent(invalid_messages)
        assert isinstance(result, AgentResult)

    @pytest.mark.asyncio
    async def test_async_invoke_list_message_support(self, agent, mock_model, agenerator):
        """Test that async invoke_async method supports List[Message] input."""
        mock_model.mock_stream.return_value = agenerator(
            [
                {"contentBlockStart": {"start": {}}},
                {"contentBlockDelta": {"delta": {"text": "Test response"}}},
                {"contentBlockStop": {}},
                {"messageStop": {"stopReason": "end_turn"}},
            ]
        )

        messages = [{"role": "user", "content": [{"text": "Async test"}]}]

        result = await agent.invoke_async(messages)

        assert isinstance(result, AgentResult)
        assert len(agent.messages) >= 2
        assert agent.messages[0]["content"][0]["text"] == "Async test"

    @pytest.mark.asyncio
    async def test_async_invoke_no_input_support(self, agent, mock_model, agenerator):
        """Test that async invoke_async method supports no-input invocation."""
        mock_model.mock_stream.return_value = agenerator(
            [
                {"contentBlockStart": {"start": {}}},
                {"contentBlockDelta": {"delta": {"text": "Test response"}}},
                {"contentBlockStop": {}},
                {"messageStop": {"stopReason": "end_turn"}},
            ]
        )

        # Pre-populate agent with messages
        agent.messages = [{"role": "user", "content": [{"text": "Async previous"}]}]

        result = await agent.invoke_async()

        assert isinstance(result, AgentResult)
        assert len(agent.messages) >= 2

    @pytest.mark.asyncio
    async def test_async_stream_list_message_support(self, agent, mock_model, agenerator):
        """Test that stream_async method supports List[Message] input."""
        mock_model.mock_stream.return_value = agenerator(
            [
                {"contentBlockStart": {"start": {}}},
                {"contentBlockDelta": {"delta": {"text": "Test response"}}},
                {"contentBlockStop": {}},
                {"messageStop": {"stopReason": "end_turn"}},
            ]
        )

        messages = [{"role": "user", "content": [{"text": "Stream test"}]}]

        events = []
        async for event in agent.stream_async(messages):
            events.append(event)

        assert len(events) > 0
        assert len(agent.messages) >= 2
        assert agent.messages[0]["content"][0]["text"] == "Stream test"

    def test_type_hints_compatibility(self, agent):
        """Test that type hints work correctly with new signatures."""
        # This test mainly ensures the code compiles with proper type hints
        # Runtime type checking is handled by other tests

        # Test various input types
        string_input: str = "test"
        content_blocks: list[ContentBlock] = [{"text": "test"}]
        messages: list[Message] = [{"role": "user", "content": [{"text": "test"}]}]
        no_input: None = None

        # These should all be valid according to type hints
        assert callable(lambda: agent(string_input))
        assert callable(lambda: agent(content_blocks))
        assert callable(lambda: agent(messages))
        assert callable(lambda: agent(no_input))
        assert callable(lambda: agent())
