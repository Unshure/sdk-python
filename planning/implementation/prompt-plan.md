# Implementation Prompt Plan

## Checklist
- [ ] Prompt 1: Update BedrockConfig with streaming parameter
- [ ] Prompt 2: Create helper methods for guardrail handling
- [ ] Prompt 3: Modify stream method to support both streaming and non-streaming
- [ ] Prompt 4: Implement _convert_non_streaming_to_streaming method
- [ ] Prompt 5: Add unit tests for streaming parameter and configuration
- [ ] Prompt 6: Add unit tests for guardrail helper methods
- [ ] Prompt 7: Add unit tests for stream method branching logic
- [ ] Prompt 8: Add unit tests for non-streaming response conversion
- [ ] Prompt 9: Add integration tests for streaming and non-streaming modes
- [ ] Prompt 10: Update README with streaming parameter documentation

## Prompts

### Prompt 1: Update BedrockConfig with streaming parameter

Update the `BedrockConfig` TypedDict in the Bedrock model provider to include a new optional `streaming` parameter with a default value of `True`. This parameter will determine whether to use the streaming or non-streaming API when calling Bedrock.

1. Add the `streaming` parameter to the `BedrockConfig` TypedDict in `src/strands/models/bedrock.py`
2. Update the class docstring to include documentation for the new parameter
3. Ensure the parameter is marked as optional with a default value of `True`

The updated `BedrockConfig` should look like this:

```python
class BedrockConfig(TypedDict, total=False):
    """Configuration options for Bedrock models.

    Attributes:
        ...existing attributes...
        streaming: Flag to enable/disable streaming. Defaults to True.
    """
    ...existing attributes...
    streaming: Optional[bool]
```

### Prompt 2: Create helper methods for guardrail handling

Create helper methods to extract and handle guardrail logic consistently across streaming and non-streaming implementations. This will improve code maintainability and ensure consistent behavior.

1. Create a method to check for blocked guardrails
2. Create a method to generate redaction events
3. Create a method to process streaming chunks with guardrail handling
4. Create a method to extract guardrail data from non-streaming responses
5. Create a method to handle Bedrock API errors consistently

Implement the following helper methods:

```python
def _has_blocked_guardrail(self, guardrail_data: dict[str, Any]) -> bool:
    """Check if guardrail data contains any blocked policies.
    
    Args:
        guardrail_data: Guardrail data from trace information.
        
    Returns:
        True if any blocked guardrail is detected, False otherwise.
    """
    if not guardrail_data:
        return False
        
    input_assessment = guardrail_data.get("inputAssessment", {})
    output_assessments = guardrail_data.get("outputAssessments", {})
    
    # Check input assessments
    if any(
        self._find_detected_and_blocked_policy(assessment)
        for assessment in input_assessment.values()
    ):
        return True
        
    # Check output assessments
    if any(
        self._find_detected_and_blocked_policy(assessment)
        for assessment in output_assessments.values()
    ):
        return True
        
    return False

def _generate_redaction_events(self) -> list[dict[str, Any]]:
    """Generate redaction events based on configuration.
    
    Returns:
        List of redaction events to yield.
    """
    events = []
    
    if self.config.get("guardrail_redact_input", True):
        logger.debug("Redacting user input due to guardrail.")
        events.append({
            "redactContent": {
                "redactUserContentMessage": self.config.get(
                    "guardrail_redact_input_message", "[User input redacted.]"
                )
            }
        })
        
    if self.config.get("guardrail_redact_output", False):
        logger.debug("Redacting assistant output due to guardrail.")
        events.append({
            "redactContent": {
                "redactAssistantContentMessage": self.config.get(
                    "guardrail_redact_output_message", "[Assistant output redacted.]"
                )
            }
        })
        
    return events

def _process_streaming_chunk(self, chunk: dict[str, Any]) -> list[dict[str, Any]]:
    """Process a streaming chunk and handle guardrails.
    
    Args:
        chunk: A chunk from the streaming response.
        
    Returns:
        List of events to yield (redaction events + the original chunk).
    """
    events = []
    
    # Check for guardrail triggers
    if (
        "metadata" in chunk
        and "trace" in chunk["metadata"]
        and "guardrail" in chunk["metadata"]["trace"]
    ):
        guardrail_data = chunk["metadata"]["trace"]["guardrail"]
        if self._has_blocked_guardrail(guardrail_data):
            events.extend(self._generate_redaction_events())
    
    # Always include the original chunk
    events.append(chunk)
    return events

def _extract_guardrail_data(self, response: dict[str, Any]) -> Optional[dict[str, Any]]:
    """Extract guardrail data from a non-streaming response.
    
    Args:
        response: The non-streaming response.
        
    Returns:
        Guardrail data if present, None otherwise.
    """
    if "trace" in response and "guardrail" in response["trace"]:
        return response["trace"]["guardrail"]
    return None

def _handle_bedrock_error(self, error: ClientError) -> None:
    """Handle Bedrock API errors consistently.
    
    Args:
        error: The ClientError from Bedrock API.
        
    Raises:
        ModelThrottledException: If throttling is detected.
        ContextWindowOverflowException: If context window overflow is detected.
        ClientError: For all other errors.
    """
    # Handle throttling
    if error.response["Error"]["Code"] == "ThrottlingException":
        raise ModelThrottledException(str(error)) from error
    
    # Handle context window overflow
    error_message = str(error)
    if any(overflow_message in error_message for overflow_message in BEDROCK_CONTEXT_WINDOW_OVERFLOW_MESSAGES):
        logger.warning("bedrock threw context window overflow error")
        raise ContextWindowOverflowException(error) from error
    
    # Re-raise all other errors
    raise error
```

### Prompt 3: Modify stream method to support both streaming and non-streaming

Refactor the `stream` method in the Bedrock model provider to support both streaming and non-streaming modes based on the `streaming` parameter in the configuration. Use the helper methods created in Prompt 2 to handle guardrails and errors consistently.

1. Extract the `streaming` parameter from the configuration with a default value of `True`
2. Add branching logic to call either the `converse_stream` API or the `converse` API
3. Use the helper methods for guardrail handling and error handling
4. For the non-streaming case, call the `_convert_non_streaming_to_streaming` method to convert the response

The updated `stream` method should look like this:

```python
def stream(self, request: dict[str, Any]) -> Iterable[dict[str, Any]]:
    """Send the request to the Bedrock model and get the response.
    
    This method calls either the Bedrock converse_stream API or the converse API
    based on the streaming parameter in the configuration.
    
    Args:
        request: The formatted request to send to the Bedrock model
        
    Returns:
        An iterable of response events from the Bedrock model
        
    Raises:
        ContextWindowOverflowException: If the input exceeds the model's context window.
        ModelThrottledException: If the model service is throttling requests.
    """
    streaming = self.config.get("streaming", True)
    
    try:
        if streaming:
            # Streaming implementation
            response = self.client.converse_stream(**request)
            for chunk in response["stream"]:
                for event in self._process_streaming_chunk(chunk):
                    yield event
        else:
            # Non-streaming implementation
            response = self.client.converse(**request)
            
            # Check for guardrail triggers before yielding any events
            guardrail_data = self._extract_guardrail_data(response)
            if guardrail_data and self._has_blocked_guardrail(guardrail_data):
                for event in self._generate_redaction_events():
                    yield event
                    
            # Convert and yield the rest of the response
            yield from self._convert_non_streaming_to_streaming(response)
    except ClientError as e:
        # Handle errors consistently
        self._handle_bedrock_error(e)
```

### Prompt 4: Implement _convert_non_streaming_to_streaming method

Implement the `_convert_non_streaming_to_streaming` method to convert non-streaming responses to the streaming format expected by the SDK. This method should simulate the sequence of events that would occur in a streaming response.

1. Create a new private method `_convert_non_streaming_to_streaming` that takes a non-streaming response and returns an iterable of events
2. Yield events in the correct sequence: messageStart, contentBlockStart, contentBlockDelta, contentBlockStop, messageStop, metadata
3. Handle different content types (text, tool use, reasoning) appropriately
4. Ensure consistent handling of metadata and trace information

```python
def _convert_non_streaming_to_streaming(self, response: dict[str, Any]) -> Iterable[dict[str, Any]]:
    """Convert a non-streaming response to the streaming format.
    
    Args:
        response: The non-streaming response from the Bedrock model.
        
    Returns:
        An iterable of response events in the streaming format.
    """
    # Note: Guardrail handling is now done before calling this method
    
    # Yield messageStart event
    yield {
        "messageStart": {
            "role": response["output"]["message"]["role"]
        }
    }
    
    # Process content blocks
    for i, content in enumerate(response["output"]["message"]["content"]):
        # Yield contentBlockStart event if needed
        if "toolUse" in content:
            yield {
                "contentBlockStart": {
                    "start": {
                        "toolUse": {
                            "toolUseId": content["toolUse"]["toolUseId"],
                            "name": content["toolUse"]["name"]
                        }
                    },
                    "contentBlockIndex": i
                }
            }
        
        # Yield contentBlockDelta event
        if "text" in content:
            yield {
                "contentBlockDelta": {
                    "delta": {
                        "text": content["text"]
                    },
                    "contentBlockIndex": i
                }
            }
        elif "toolUse" in content:
            yield {
                "contentBlockDelta": {
                    "delta": {
                        "toolUse": {
                            "input": content["toolUse"]["input"]
                        }
                    },
                    "contentBlockIndex": i
                }
            }
        elif "reasoningContent" in content:
            yield {
                "contentBlockDelta": {
                    "delta": {
                        "reasoningContent": {
                            "text": content["reasoningContent"]["reasoningText"]["text"],
                            "signature": content["reasoningContent"]["reasoningText"].get("signature"),
                            "redactedContent": content["reasoningContent"].get("redactedContent")
                        }
                    },
                    "contentBlockIndex": i
                }
            }
        
        # Yield contentBlockStop event
        yield {
            "contentBlockStop": {
                "contentBlockIndex": i
            }
        }
    
    # Yield messageStop event
    yield {
        "messageStop": {
            "stopReason": response["stopReason"],
            "additionalModelResponseFields": response.get("additionalModelResponseFields")
        }
    }
    
    # Yield metadata event
    if "usage" in response or "metrics" in response or "trace" in response:
        metadata = {"metadata": {}}
        if "usage" in response:
            metadata["metadata"]["usage"] = response["usage"]
        if "metrics" in response:
            metadata["metadata"]["metrics"] = response["metrics"]
        if "trace" in response:
            metadata["metadata"]["trace"] = response["trace"]
        yield metadata
```

### Prompt 5: Add unit tests for streaming parameter and configuration

Add unit tests to verify that the `streaming` parameter is correctly set in the configuration and that the default value is `True` when not specified.

1. Create a test case that verifies the default value of the `streaming` parameter
2. Create a test case that verifies the `streaming` parameter can be set to `False`
3. Create a test case that verifies the `streaming` parameter can be updated after initialization

```python
def test_streaming_parameter_default():
    """Test that the streaming parameter defaults to True."""
    model = BedrockModel(model_id="test-model")
    assert model.config.get("streaming", None) is None  # Not explicitly set
    
def test_streaming_parameter_set_false():
    """Test that the streaming parameter can be set to False."""
    model = BedrockModel(model_id="test-model", streaming=False)
    assert model.config.get("streaming") is False
    
def test_streaming_parameter_update():
    """Test that the streaming parameter can be updated."""
    model = BedrockModel(model_id="test-model")
    model.update_config(streaming=False)
    assert model.config.get("streaming") is False
```

### Prompt 6: Add unit tests for guardrail helper methods

Add unit tests to verify that the guardrail helper methods work correctly.

1. Create test cases for `_has_blocked_guardrail` with various guardrail data
2. Create test cases for `_generate_redaction_events` with different configurations
3. Create test cases for `_process_streaming_chunk` with chunks containing guardrail data
4. Create test cases for `_extract_guardrail_data` with different response structures

```python
def test_has_blocked_guardrail_with_blocked_input():
    """Test _has_blocked_guardrail with blocked input assessment."""
    model = BedrockModel(model_id="test-model")
    guardrail_data = {
        "inputAssessment": {
            "test": {
                "action": "BLOCKED",
                "detected": True
            }
        }
    }
    assert model._has_blocked_guardrail(guardrail_data) is True
    
def test_has_blocked_guardrail_with_blocked_output():
    """Test _has_blocked_guardrail with blocked output assessment."""
    model = BedrockModel(model_id="test-model")
    guardrail_data = {
        "outputAssessments": {
            "test": [
                {
                    "contentPolicy": {
                        "filters": [
                            {
                                "action": "BLOCKED",
                                "detected": True
                            }
                        ]
                    }
                }
            ]
        }
    }
    assert model._has_blocked_guardrail(guardrail_data) is True
    
def test_has_blocked_guardrail_with_no_blocked():
    """Test _has_blocked_guardrail with no blocked policies."""
    model = BedrockModel(model_id="test-model")
    guardrail_data = {
        "inputAssessment": {
            "test": {
                "action": "NONE",
                "detected": False
            }
        }
    }
    assert model._has_blocked_guardrail(guardrail_data) is False
    
def test_generate_redaction_events_default():
    """Test _generate_redaction_events with default configuration."""
    model = BedrockModel(model_id="test-model")
    events = model._generate_redaction_events()
    assert len(events) == 1
    assert "redactContent" in events[0]
    assert "redactUserContentMessage" in events[0]["redactContent"]
    
def test_generate_redaction_events_custom_messages():
    """Test _generate_redaction_events with custom redaction messages."""
    model = BedrockModel(
        model_id="test-model",
        guardrail_redact_input=True,
        guardrail_redact_output=True,
        guardrail_redact_input_message="Custom input redaction",
        guardrail_redact_output_message="Custom output redaction"
    )
    events = model._generate_redaction_events()
    assert len(events) == 2
    assert events[0]["redactContent"]["redactUserContentMessage"] == "Custom input redaction"
    assert events[1]["redactContent"]["redactAssistantContentMessage"] == "Custom output redaction"
```

### Prompt 7: Add unit tests for stream method branching logic

Add unit tests to verify that the `stream` method correctly branches based on the `streaming` parameter and calls the appropriate API.

1. Create a test case that verifies the `converse_stream` API is called when `streaming` is `True`
2. Create a test case that verifies the `converse` API is called when `streaming` is `False`
3. Create a test case that verifies the helper methods are called appropriately

```python
@patch("boto3.Session")
def test_stream_with_streaming_true(mock_session):
    """Test stream method with streaming=True."""
    # Setup mock
    mock_client = MagicMock()
    mock_session.return_value.client.return_value = mock_client
    mock_client.converse_stream.return_value = {"stream": [{"chunk": {"bytes": "test"}}]}
    
    # Create model and call stream
    model = BedrockModel(model_id="test-model", streaming=True)
    request = {"modelId": "test-model"}
    list(model.stream(request))
    
    # Verify converse_stream was called
    mock_client.converse_stream.assert_called_once_with(**request)
    mock_client.converse.assert_not_called()
    
@patch("boto3.Session")
def test_stream_with_streaming_false(mock_session):
    """Test stream method with streaming=False."""
    # Setup mock
    mock_client = MagicMock()
    mock_session.return_value.client.return_value = mock_client
    mock_client.converse.return_value = {
        "output": {
            "message": {
                "role": "assistant",
                "content": [{"text": "test"}]
            }
        },
        "stopReason": "end_turn"
    }
    
    # Create model and call stream
    model = BedrockModel(model_id="test-model", streaming=False)
    request = {"modelId": "test-model"}
    list(model.stream(request))
    
    # Verify converse was called
    mock_client.converse.assert_called_once_with(**request)
    mock_client.converse_stream.assert_not_called()
```

### Prompt 8: Add unit tests for non-streaming response conversion

Add unit tests to verify that the `_convert_non_streaming_to_streaming` method correctly converts non-streaming responses to the streaming format.

1. Create test cases for different content types (text, tool use, reasoning)
2. Create test cases for metadata and trace information
3. Verify that the events are yielded in the correct sequence

```python
def test_convert_non_streaming_text_content():
    """Test converting non-streaming response with text content."""
    model = BedrockModel(model_id="test-model")
    response = {
        "output": {
            "message": {
                "role": "assistant",
                "content": [{"text": "Hello, world!"}]
            }
        },
        "stopReason": "end_turn"
    }
    
    events = list(model._convert_non_streaming_to_streaming(response))
    
    # Verify events
    assert len(events) == 4
    assert events[0] == {"messageStart": {"role": "assistant"}}
    assert events[1] == {"contentBlockDelta": {"delta": {"text": "Hello, world!"}, "contentBlockIndex": 0}}
    assert events[2] == {"contentBlockStop": {"contentBlockIndex": 0}}
    assert events[3] == {"messageStop": {"stopReason": "end_turn", "additionalModelResponseFields": None}}
    
def test_convert_non_streaming_tool_use():
    """Test converting non-streaming response with tool use."""
    model = BedrockModel(model_id="test-model")
    response = {
        "output": {
            "message": {
                "role": "assistant",
                "content": [{
                    "toolUse": {
                        "toolUseId": "123",
                        "name": "test_tool",
                        "input": {"param": "value"}
                    }
                }]
            }
        },
        "stopReason": "tool_use"
    }
    
    events = list(model._convert_non_streaming_to_streaming(response))
    
    # Verify events
    assert len(events) == 5
    assert events[0] == {"messageStart": {"role": "assistant"}}
    assert events[1] == {
        "contentBlockStart": {
            "start": {
                "toolUse": {
                    "toolUseId": "123",
                    "name": "test_tool"
                }
            },
            "contentBlockIndex": 0
        }
    }
    assert events[2] == {
        "contentBlockDelta": {
            "delta": {
                "toolUse": {
                    "input": {"param": "value"}
                }
            },
            "contentBlockIndex": 0
        }
    }
    assert events[3] == {"contentBlockStop": {"contentBlockIndex": 0}}
    assert events[4] == {"messageStop": {"stopReason": "tool_use", "additionalModelResponseFields": None}}
```

### Prompt 9: Add integration tests for streaming and non-streaming modes

Add integration tests to verify that the Bedrock model provider works correctly in both streaming and non-streaming modes.

1. Create an integration test that uses the streaming mode (default)
2. Create an integration test that uses the non-streaming mode
3. Verify that both modes produce the expected results
4. Test error handling in both modes

```python
@pytest.mark.integ
def test_bedrock_streaming_integration():
    """Integration test for Bedrock model with streaming=True."""
    model = BedrockModel(model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0", streaming=True)
    messages = [{"role": "user", "content": [{"text": "Hello"}]}]
    
    # Call converse and collect events
    events = list(model.converse(messages))
    
    # Verify basic structure of events
    assert any("messageStart" in event for event in events)
    assert any("contentBlockDelta" in event for event in events)
    assert any("messageStop" in event for event in events)
    
@pytest.mark.integ
def test_bedrock_non_streaming_integration():
    """Integration test for Bedrock model with streaming=False."""
    model = BedrockModel(model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0", streaming=False)
    messages = [{"role": "user", "content": [{"text": "Hello"}]}]
    
    # Call converse and collect events
    events = list(model.converse(messages))
    
    # Verify basic structure of events
    assert any("messageStart" in event for event in events)
    assert any("contentBlockDelta" in event for event in events)
    assert any("messageStop" in event for event in events)
```

### Prompt 10: Update README with streaming parameter documentation

Update the README to document the new `streaming` parameter and provide examples of how to use it.

1. Add a new section to the README about streaming support
2. Explain the default behavior (streaming enabled)
3. Provide an example of how to disable streaming
4. Mention that not all Bedrock models support streaming

```markdown
### Streaming Support

The Bedrock model provider supports both streaming and non-streaming modes. By default, streaming is enabled. To disable streaming:

```python
from strands import Agent
from strands.models import BedrockModel

# Disable streaming
bedrock_model = BedrockModel(
    model_id="us.amazon.nova-pro-v1:0",
    streaming=False
)
agent = Agent(model=bedrock_model)
```

Note that not all Bedrock models support streaming. If you're using a model that doesn't support streaming, you should set `streaming=False`.
```
