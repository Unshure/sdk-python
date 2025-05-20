# Research: Bedrock Model Implementation

## Current Implementation

The current implementation of the Bedrock model provider in the Strands Agents SDK is defined in `/workplace/ncclegg/sdk-python/src/strands/models/bedrock.py`. The key components are:

1. **BedrockModel Class**: Implements the abstract `Model` class defined in `/workplace/ncclegg/sdk-python/src/strands/types/models.py`.

2. **BedrockConfig TypedDict**: Contains configuration options for Bedrock models, including:
   - `model_id`: The Bedrock model ID
   - Various parameters like `temperature`, `max_tokens`, etc.
   - Guardrail configuration options
   - Cache point configuration

3. **Key Methods**:
   - `__init__`: Initializes the Bedrock model provider with configuration options
   - `update_config`: Updates the model configuration
   - `get_config`: Returns the current model configuration
   - `format_request`: Formats a request to the Bedrock model
   - `format_chunk`: Formats response chunks from the model
   - `stream`: Sends a request to the model and returns a streaming response

4. **Streaming Implementation**:
   - Currently, the `stream` method calls the Bedrock `converse_stream` API
   - It handles guardrail assessments and redaction
   - It handles errors like context window overflow and throttling

## Model Abstract Class

The `Model` abstract base class in `/workplace/ncclegg/sdk-python/src/strands/types/models.py` defines the interface that all model implementations must follow:

1. **Abstract Methods**:
   - `update_config`: Update the model configuration
   - `get_config`: Get the model configuration
   - `format_request`: Format a request to the model
   - `format_chunk`: Format response chunks from the model
   - `stream`: Send a request to the model and get a streaming response

2. **Concrete Methods**:
   - `converse`: High-level method that handles the full lifecycle of conversing with the model:
     1. Format the request
     2. Send the request to the model
     3. Yield formatted message chunks

## Implementation Considerations

To implement support for both streaming and non-streaming in the Bedrock model provider, we need to:

1. **Update BedrockConfig**:
   - Add a new `streaming` parameter (default: `True`)

2. **Modify the `stream` Method**:
   - Add branching logic based on the `streaming` parameter
   - If `streaming` is `True`, use the existing `converse_stream` API
   - If `streaming` is `False`, use the `converse` API and convert the response to a streaming format

3. **Response Conversion**:
   - When using the non-streaming API, we need to convert the response to match the streaming format
   - This involves yielding events derived from the non-streaming response

4. **Error Handling**:
   - Ensure consistent error handling between streaming and non-streaming implementations
   - Handle context window overflow and throttling in both cases

## Bedrock API Differences

The Bedrock API has two main endpoints for model invocation:

1. **converse_stream**:
   - Returns a streaming response with chunks of the model's output
   - Used when real-time, token-by-token responses are needed

2. **converse**:
   - Returns a complete response with the model's entire output
   - Used when the complete response is needed at once

Both APIs accept similar parameters, but the response format differs. The implementation will need to handle these differences and provide a consistent interface to the rest of the SDK.
