from app.services.ai.providers.responses_adapter import parse_response

def test_function_call_and_reasoning_preserved():
    items = [{"type": "reasoning", "encrypted_content": "example"}, {"type": "function_call", "id": "fc_1", "call_id": "call_1", "name": "marketing_capacity", "arguments": "{}"}]
    choice, returned, usage = parse_response({"status": "completed", "output": items, "usage": {"input_tokens": 22, "output_tokens": 10}})
    assert returned == items
    assert choice["tool_calls"][0]["id"] == "call_1"
    assert usage == {"prompt_tokens": 22, "completion_tokens": 10}

def test_text():
    choice, _, _ = parse_response({"output": [{"type": "message", "content": [{"type": "output_text", "text": "hello"}]}]})
    assert choice["content"] == "hello"
