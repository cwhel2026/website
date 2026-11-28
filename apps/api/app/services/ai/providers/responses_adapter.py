"""Transport adapter for stateless Responses API tool loops."""
async def request_response(client, key, model, messages, specs):
    tools = [{"type": "function", **spec["function"], "strict": False} for spec in specs]
    response = await client.post(
        "https://api.openai.com/v1/responses",
        headers={"Authorization": f"Bearer {key}"},
        json={"model": model, "input": messages, "tools": tools, "tool_choice": "auto",
              "store": False, "include": ["reasoning.encrypted_content"], "max_output_tokens": 4000},
    )
    response.raise_for_status()
    return response.json()

def parse_response(payload):
    if payload.get("status") not in (None, "completed"):
        raise RuntimeError("OpenAI response incomplete")
    items = payload.get("output", [])
    texts, calls = [], []
    for item in items:
        if item.get("type") == "message":
            texts.extend(part["text"] for part in item.get("content", []) if part.get("type") == "output_text")
        elif item.get("type") == "function_call":
            calls.append({"id": item["call_id"], "function": {"name": item["name"], "arguments": item["arguments"]}})
    usage = payload.get("usage") or {}
    return {"content": "\n".join(texts), "tool_calls": calls}, items, {
        "prompt_tokens": usage.get("input_tokens", 0),
        "completion_tokens": usage.get("output_tokens", 0),
    }
