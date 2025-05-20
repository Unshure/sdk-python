# Idea Honing: Bedrock Model Provider Streaming Support

This document contains the requirements clarification process for implementing both streaming and non-streaming support in the Bedrock model provider.

## Question 1
Which specific Bedrock models need to be supported, and which ones currently support streaming versus non-streaming?

### Answer
All models need to be supported. When the customer provides a model with the `model_id` parameter, they can optionally include a `streaming` parameter that defaults to True. If they set it to false, the Bedrock model provider will use the `converse` api instead of the `converse_stream` api.

## Question 2
How should the SDK handle the case where a user requests streaming for a model that doesn't support it? Should it automatically fall back to non-streaming or raise an error?

### Answer
The SDK should have no logic to handle this case. If the customer specifies a non-streaming model, but does not update the `streaming` parameter, then the SDK should make the call to the `converse_stream` API, and then return the error message from Bedrock.

## Question 3
How should the current implementation of the Bedrock model provider be modified? Should we update the existing class or create a new implementation?

### Answer
The existing Bedrock model provider class should be updated to support this feature.

## Question 4
How should the API for the Bedrock model provider be modified to support the streaming parameter? Should it be added to the constructor, or should there be a separate method for setting it?

### Answer
The `BedrockConfig` subclass of the `BedrockModel` class should be updated to contain a new optional `streaming` parameter in the constructor. This parameter will be used to trigger branching logic when calling the API.

## Question 5
What should be the default value for the streaming parameter, and should there be any validation for this parameter?

### Answer
The default value for the streaming parameter should be True.

## Question 6
How should the implementation handle the non-streaming case? Should it convert the response to match the streaming format, or should it return a different format?

### Answer
When handling the non-streaming case, the implementation should convert the response to a streaming format. The SDK expects an iterator response, so after receiving the response, the implementation can `yield` each of the expected events that are derived from the non-streaming response.

## Question 7
Are there any specific tests that should be added or modified to verify the new functionality?

### Answer
Yes, unit and integration tests should be added for this implementation.

## Question 8
What documentation updates are needed to communicate this new feature to users?

### Answer
An update to the README of the package is all that will be required for this change.

## Question 9
Are there any backward compatibility concerns with this change?

### Answer
No, there are no backward compatibility concerns with this change.
