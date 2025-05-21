import unittest.mock
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from strands.models import BedrockModel
from strands.types.exceptions import ContextWindowOverflowException, ModelThrottledException


@pytest.fixture
def bedrock_client():
    with unittest.mock.patch("boto3.Session") as mock_session_cls:
        yield mock_session_cls.return_value.client.return_value


@pytest.fixture
def model_id():
    return "test-model"


@pytest.fixture
def model(bedrock_client, model_id):
    _ = bedrock_client
    return BedrockModel(model_id=model_id)


def test_streaming_parameter_default(model):
    """Test that the streaming parameter defaults to None (not explicitly set)."""
    assert model.config.get("streaming") is None


def test_streaming_parameter_set_false():
    """Test that the streaming parameter can be set to False."""
    model = BedrockModel(model_id="test-model", streaming=False)
    assert model.config.get("streaming") is False


def test_streaming_parameter_set_true():
    """Test that the streaming parameter can be set to True."""
    model = BedrockModel(model_id="test-model", streaming=True)
    assert model.config.get("streaming") is True


def test_streaming_parameter_update(model):
    """Test that the streaming parameter can be updated."""
    model.update_config(streaming=False)
    assert model.config.get("streaming") is False
    model.update_config(streaming=True)
    assert model.config.get("streaming") is True


def test_has_blocked_guardrail_with_blocked_input(model):
    """Test _has_blocked_guardrail with blocked input assessment."""
    guardrail_data = {
        "inputAssessment": {
            "test": {
                "action": "BLOCKED",
                "detected": True
            }
        }
    }
    assert model._has_blocked_guardrail(guardrail_data) is True


def test_has_blocked_guardrail_with_blocked_output(model):
    """Test _has_blocked_guardrail with blocked output assessment."""
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


def test_has_blocked_guardrail_with_no_blocked(model):
    """Test _has_blocked_guardrail with no blocked policies."""
    guardrail_data = {
        "inputAssessment": {
            "test": {
                "action": "NONE",
                "detected": False
            }
        }
    }
    assert model._has_blocked_guardrail(guardrail_data) is False


def test_has_blocked_guardrail_with_empty_data(model):
    """Test _has_blocked_guardrail with empty data."""
    assert model._has_blocked_guardrail({}) is False
    assert model._has_blocked_guardrail(None) is False


def test_generate_redaction_events_default(model):
    """Test _generate_redaction_events with default configuration."""
    events = model._generate_redaction_events()
    assert len(events) == 1
    assert "redactContent" in events[0]
    assert "redactUserContentMessage" in events[0]["redactContent"]
    assert events[0]["redactContent"]["redactUserContentMessage"] == "[User input redacted.]"


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


def test_generate_redaction_events_disabled():
    """Test _generate_redaction_events with redaction disabled."""
    model = BedrockModel(
        model_id="test-model",
        guardrail_redact_input=False,
        guardrail_redact_output=False
    )
    events = model._generate_redaction_events()
    assert len(events) == 0


def test_process_streaming_chunk_no_guardrail(model):
    """Test _process_streaming_chunk with no guardrail data."""
    chunk = {"chunk": {"bytes": "test"}}
    events = model._process_streaming_chunk(chunk)
    assert len(events) == 1
    assert events[0] == chunk


def test_process_streaming_chunk_with_guardrail_no_blocked(model):
    """Test _process_streaming_chunk with guardrail data but no blocked policies."""
    chunk = {
        "metadata": {
            "trace": {
                "guardrail": {
                    "inputAssessment": {
                        "test": {
                            "action": "NONE",
                            "detected": False
                        }
                    }
                }
            }
        }
    }
    events = model._process_streaming_chunk(chunk)
    assert len(events) == 1
    assert events[0] == chunk


def test_process_streaming_chunk_with_blocked_guardrail(model):
    """Test _process_streaming_chunk with blocked guardrail."""
    chunk = {
        "metadata": {
            "trace": {
                "guardrail": {
                    "inputAssessment": {
                        "test": {
                            "action": "BLOCKED",
                            "detected": True
                        }
                    }
                }
            }
        }
    }
    events = model._process_streaming_chunk(chunk)
    assert len(events) == 2
    assert "redactContent" in events[0]
    assert events[1] == chunk


def test_extract_guardrail_data(model):
    """Test _extract_guardrail_data with guardrail data."""
    response = {
        "trace": {
            "guardrail": {
                "inputAssessment": {
                    "test": {
                        "action": "BLOCKED",
                        "detected": True
                    }
                }
            }
        }
    }
    guardrail_data = model._extract_guardrail_data(response)
    assert guardrail_data == response["trace"]["guardrail"]


def test_extract_guardrail_data_no_guardrail(model):
    """Test _extract_guardrail_data with no guardrail data."""
    response = {"trace": {}}
    guardrail_data = model._extract_guardrail_data(response)
    assert guardrail_data is None

    response = {}
    guardrail_data = model._extract_guardrail_data(response)
    assert guardrail_data is None


def test_handle_bedrock_error_throttling(model):
    """Test _handle_bedrock_error with throttling error."""
    error = ClientError(
        error_response={"Error": {"Code": "ThrottlingException", "Message": "Rate exceeded"}},
        operation_name="converse"
    )
    with pytest.raises(ModelThrottledException):
        model._handle_bedrock_error(error)


def test_handle_bedrock_error_context_window(model):
    """Test _handle_bedrock_error with context window overflow."""
    error = ClientError(
        error_response={"Error": {"Code": "ValidationException", "Message": "Input is too long for requested model"}},
        operation_name="converse"
    )
    with pytest.raises(ContextWindowOverflowException):
        model._handle_bedrock_error(error)


def test_handle_bedrock_error_other(model):
    """Test _handle_bedrock_error with other error."""
    error = ClientError(
        error_response={"Error": {"Code": "ValidationException", "Message": "Other error"}},
        operation_name="converse"
    )
    with pytest.raises(ClientError):
        model._handle_bedrock_error(error)


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


def test_convert_non_streaming_text_content(model):
    """Test converting non-streaming response with text content."""
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


def test_convert_non_streaming_tool_use(model):
    """Test converting non-streaming response with tool use."""
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


def test_convert_non_streaming_with_metadata(model):
    """Test converting non-streaming response with metadata."""
    response = {
        "output": {
            "message": {
                "role": "assistant",
                "content": [{"text": "Hello"}]
            }
        },
        "stopReason": "end_turn",
        "usage": {
            "inputTokens": 10,
            "outputTokens": 20,
            "totalTokens": 30
        },
        "metrics": {
            "latencyMs": 100
        }
    }
    
    events = list(model._convert_non_streaming_to_streaming(response))
    
    # Verify events
    assert len(events) == 5
    assert events[0] == {"messageStart": {"role": "assistant"}}
    assert events[1] == {"contentBlockDelta": {"delta": {"text": "Hello"}, "contentBlockIndex": 0}}
    assert events[2] == {"contentBlockStop": {"contentBlockIndex": 0}}
    assert events[3] == {"messageStop": {"stopReason": "end_turn", "additionalModelResponseFields": None}}
    assert "metadata" in events[4]
    assert events[4]["metadata"]["usage"] == response["usage"]
    assert events[4]["metadata"]["metrics"] == response["metrics"]
