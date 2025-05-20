# Detailed Design: Bedrock Model Provider Streaming Support

## Overview

This design document outlines the implementation of both streaming and non-streaming support in the Bedrock model provider for the Strands Agents SDK. The goal is to allow users to choose between streaming and non-streaming modes when using Bedrock models, as not all Bedrock models support streaming.

## Requirements

1. Update the `BedrockConfig` class to include a new optional `streaming` parameter with a default value of `True`.
2. Modify the `stream` method to support both streaming and non-streaming modes based on the `streaming` parameter.
3. When using non-streaming mode, convert the response to match the streaming format expected by the SDK.
4. Maintain consistent error handling between streaming and non-streaming implementations.
5. Update the README to document this new feature.
6. Add unit and integration tests for the new functionality.

## Architecture

The implementation will maintain the existing architecture of the Bedrock model provider, with modifications to support both streaming and non-streaming modes. The key components are:

1. **BedrockModel Class**: The main class implementing the Model interface.
2. **BedrockConfig TypedDict**: Configuration options for Bedrock models.
3. **stream Method**: The method that sends requests to the Bedrock API and returns responses.
4. **_convert_non_streaming_to_streaming Method**: A new private method to convert non-streaming responses to streaming format.

## Components and Interfaces

### BedrockConfig

The `BedrockConfig` TypedDict will be updated to include a new optional `streaming` parameter:

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

### stream Method

The `stream` method will be modified to support both streaming and non-streaming modes:

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
        EventStreamError: For all other Bedrock API errors.
    """
    streaming = self.config.get("streaming", True)
    
    try:
        if streaming:
            # Existing streaming implementation
            response = self.client.converse_stream(**request)
            for chunk in response["stream"]:
                # Existing guardrail handling
                yield chunk
        else:
            # Non-streaming implementation
            response = self.client.converse(**request)
            # Convert non-streaming response to streaming format
            yield from self._convert_non_streaming_to_streaming(response)
    except (EventStreamError, ClientError) as e:
        # Existing error handling
        # ...
```

### _convert_non_streaming_to_streaming Method

A new private method will be added to convert non-streaming responses to the streaming format:

```python
def _convert_non_streaming_to_streaming(self, response: dict[str, Any]) -> Iterable[dict[str, Any]]:
    """Convert a non-streaming response to the streaming format.

    Args:
        response: The non-streaming response from the Bedrock model.

    Returns:
        An iterable of response events in the streaming format.
    """
    # Check for guardrail redaction
    if "trace" in response and "guardrail" in response["trace"]:
        input_assessment = response["trace"]["guardrail"].get("inputAssessment", {})
        output_assessments = response["trace"]["guardrail"].get("outputAssessments", {})
        
        # Check if an input or output guardrail was triggered
        if any(
            self._find_detected_and_blocked_policy(assessment)
            for assessment in input_assessment.values()
        ) or any(
            self._find_detected_and_blocked_policy(assessment)
            for assessment in output_assessments.values()
        ):
            if self.config.get("guardrail_redact_input", True):
                yield {
                    "redactContent": {
                        "redactUserContentMessage": self.config.get(
                            "guardrail_redact_input_message", "[User input redacted.]"
                        )
                    }
                }
            if self.config.get("guardrail_redact_output", False):
                yield {
                    "redactContent": {
                        "redactAssistantContentMessage": self.config.get(
                            "guardrail_redact_output_message", "[Assistant output redacted.]"
                        )
                    }
                }
    
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

## Data Models

No new data models are required for this implementation. The existing data models and types will be used.

## Error Handling

The error handling will be consistent between streaming and non-streaming implementations:

1. **Context Window Overflow**: Detected by checking for specific error messages and raising `ContextWindowOverflowException`.
2. **Throttling**: Detected by checking for "ThrottlingException" in the error message and raising `ModelThrottledException`.
3. **Other Errors**: Propagated as-is.

For the non-streaming implementation, we need to handle errors that might occur during the conversion process:

```python
try:
    response = self.client.converse(**request)
    yield from self._convert_non_streaming_to_streaming(response)
except ClientError as e:
    # Handle throttling that occurs at the beginning of the call
    if e.response["Error"]["Code"] == "ThrottlingException":
        raise ModelThrottledException(str(e)) from e
    
    # Handle context window overflow
    error_message = str(e)
    if any(overflow_message in error_message for overflow_message in BEDROCK_CONTEXT_WINDOW_OVERFLOW_MESSAGES):
        logger.warning("bedrock threw context window overflow error")
        raise ContextWindowOverflowException(e) from e
    
    raise
```

## Testing Strategy

### Unit Tests

1. **Configuration Tests**:
   - Test that the `streaming` parameter is correctly set in the configuration.
   - Test default value (True) when not specified.

2. **Stream Method Tests**:
   - Test branching logic based on the `streaming` parameter.
   - Test that the correct API (converse_stream or converse) is called.

3. **Conversion Tests**:
   - Test that non-streaming responses are correctly converted to the streaming format.
   - Test handling of different content types (text, tool use, reasoning).
   - Test handling of guardrail assessments in non-streaming responses.

### Integration Tests

1. **End-to-End Tests**:
   - Test with streaming enabled (default).
   - Test with streaming disabled.
   - Test with models that support and don't support streaming.

2. **Error Handling Tests**:
   - Test context window overflow in both streaming and non-streaming modes.
   - Test throttling in both streaming and non-streaming modes.

## Implementation Approach

1. Update the `BedrockConfig` TypedDict to include the new `streaming` parameter.
2. Modify the `stream` method to support both streaming and non-streaming modes.
3. Implement the `_convert_non_streaming_to_streaming` method.
4. Update error handling to work consistently in both modes.
5. Add unit and integration tests for the new functionality.
6. Update the README to document this new feature.

## Documentation Updates

The README will be updated to include information about the new `streaming` parameter:

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
