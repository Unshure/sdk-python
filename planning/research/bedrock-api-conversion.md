# Research: Converting Bedrock Non-Streaming to Streaming Format

## API Response Formats

### Converse Stream API

The `converse_stream` API returns an EventStream where each event contains one of the following top-level keys:

1. `messageStart`: Indicates the start of a message with a role (user/assistant)
2. `contentBlockStart`: Indicates the start of a content block (e.g., text, tool use)
3. `contentBlockDelta`: Contains incremental content updates (text, tool use input, reasoning)
4. `contentBlockStop`: Indicates the end of a content block
5. `messageStop`: Indicates the end of a message with a stop reason
6. `metadata`: Contains usage, metrics, and trace information
7. `redactContent`: Used to redact user or assistant content when guardrails are triggered
8. Various exception events: For error handling

### Converse API

The `converse` API returns a complete response with the following structure:

1. `output.message`: Contains the complete message with role and content
2. `output.message.content`: Array of content blocks (text, tool use, etc.)
3. `stopReason`: Reason why the model stopped generating content
4. `usage`: Token usage information
5. `metrics`: Performance metrics
6. `trace`: Trace information for debugging and monitoring

## Conversion Strategy

To convert a non-streaming response to a streaming format, we need to simulate the sequence of events that would occur in a streaming response:

1. **messageStart Event**:
   - Extract the role from `response["output"]["message"]["role"]`

2. **contentBlockStart Events**:
   - For each content block in `response["output"]["message"]["content"]`
   - Generate a contentBlockStart event if needed (e.g., for tool use)

3. **contentBlockDelta Events**:
   - For each content block in `response["output"]["message"]["content"]`
   - Generate a contentBlockDelta event with the appropriate content type (text, tool use, reasoning)

4. **contentBlockStop Events**:
   - For each content block in `response["output"]["message"]["content"]`
   - Generate a contentBlockStop event

5. **messageStop Event**:
   - Extract the stop reason from `response["stopReason"]`
   - Include any additional model response fields

6. **metadata Event**:
   - Extract usage, metrics, and trace information from the response

7. **redactContent Event**:
   - If guardrails are triggered, generate redactContent events
   - This requires checking the trace information for blocked policies
   - Use the configured redact messages from the model config

## Implementation Considerations

### Content Block Handling

The `converse` API returns complete content blocks, while the `converse_stream` API returns incremental updates. When converting:

1. For text content, we need to yield the entire text as a single delta
2. For tool use, we need to yield the tool name and input as separate events
3. For reasoning content, we need to handle the different structure between APIs

### Error Handling

Both APIs have different error structures:

1. The `converse_stream` API includes error events in the stream
2. The `converse` API throws exceptions

We need to ensure consistent error handling between both approaches.

### Guardrail Handling

Both APIs include guardrail information, but in different formats:

1. The `converse_stream` API includes guardrail assessments in the metadata events
2. The `converse` API includes guardrail information in the trace field

For guardrail redaction, we need to:
1. Check if guardrails are triggered in the trace information
2. Generate redactContent events with the appropriate messages
3. Use the same logic as the streaming implementation to detect blocked policies

## RedactContent Event

The `redactContent` event is used to redact user or assistant content when guardrails are triggered. It has the following structure:

```python
class RedactContentEvent(TypedDict):
    """Event for redacting content.

    Attributes:
        redactUserContentMessage: The string to overwrite the users input with.
        redactAssistantContentMessage: The string to overwrite the assistants output with.
    """
    redactUserContentMessage: Optional[str]
    redactAssistantContentMessage: Optional[str]
```

In the current implementation, redactContent events are generated when:
1. Guardrail assessments are detected in the metadata
2. The assessment contains a detected and blocked policy
3. The model is configured to redact input (`guardrail_redact_input`) or output (`guardrail_redact_output`)

For the non-streaming implementation, we need to:
1. Check the trace information for guardrail assessments
2. Use the `_find_detected_and_blocked_policy` method to detect blocked policies
3. Generate redactContent events with the configured messages

## Code Structure

The conversion function should:

1. Take a complete `converse` response as input
2. Yield a series of events that match the `converse_stream` format
3. Handle all content types and edge cases
4. Maintain compatibility with the existing `format_chunk` method
5. Handle guardrail redaction consistently with the streaming implementation

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
    
    # 1. Yield messageStart event
    yield {
        "messageStart": {
            "role": response["output"]["message"]["role"]
        }
    }

    # 2 & 3. Yield contentBlockStart and contentBlockDelta events
    for i, content in enumerate(response["output"]["message"]["content"]):
        # Handle different content types (text, tool use, reasoning)
        # ...

    # 4. Yield contentBlockStop events
    for i, _ in enumerate(response["output"]["message"]["content"]):
        yield {
            "contentBlockStop": {
                "contentBlockIndex": i
            }
        }

    # 5. Yield messageStop event
    yield {
        "messageStop": {
            "stopReason": response["stopReason"],
            "additionalModelResponseFields": response.get("additionalModelResponseFields")
        }
    }

    # 6. Yield metadata event
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
