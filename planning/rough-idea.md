# Rough Idea: Bedrock Model Provider Streaming Support

I would like to update the bedrock model provider in the sdk-python repo to have support for both a streaming `converse_stream` and non-streaming `converse` implementation. This is because not all bedrock models support streaming, so we should support both types of models in this sdk.
