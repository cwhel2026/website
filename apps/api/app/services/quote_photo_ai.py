"""Vision assessment for driveway photographs.

The result never changes a quotation price and never claims a structural conclusion.
If the provider is missing or fails, the caller still has the provisional estimate.
"""

from __future__ import annotations

import base64
import json
import logging
from typing import Any

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)

ALLOWED = {"normal_wear", "edge_wear", "crack", "pothole", "unsuitable", "unclear"}
SIGNIFICANT = {"crack", "pothole", "unsuitable"}

_SYSTEM = (
    "You assess driveway photographs for a restoration company. "
    "Reply with JSON only: "
    '{"findings":[{"kind":"normal_wear|edge_wear|crack|pothole|unsuitable|unclear","note":"short"}]}. '
    "normal_wear is fading and ordinary surface wear. "
    "edge_wear is minor deterioration around edges. "
    "crack means a crack that may need filling. "
    "pothole is a hole or other significant damage. "
    "unsuitable means the surface may not suit a straightforward restoration. "
    "Do not give a price. Do not say the structure is sound or unsound. "
    "Minor cosmetic wear is not a reason to add a charge."
)


def interpret_findings(raw: list[Any]) -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        kind = str(item.get("kind") or "unclear")
        if kind not in ALLOWED:
            kind = "unclear"
        findings.append({"kind": kind, "note": str(item.get("note") or "")[:240]})
    review = any(item["kind"] in SIGNIFICANT for item in findings)
    return {
        "status": "assessed",
        "findings": findings,
        "review_required": review,
        "summary": customer_summary(findings, review),
        "changes_price": False,
    }


def customer_summary(findings: list[dict[str, str]], review: bool) -> str:
    if review:
        return (
            "A photograph may show a crack, pothole or a surface that needs a closer look. "
            "That is flagged for review. The estimate is unchanged, and any repair is priced only after approval. "
            "A photograph cannot confirm structural condition."
        )
    if not findings:
        return "Photograph saved. It has not changed the estimate."
    return (
        "The photographs look like normal fading, surface wear or minor edge deterioration. "
        "That does not add a charge. The estimate is unchanged."
    )


def unavailable_assessment() -> dict[str, Any]:
    return {
        "status": "unavailable",
        "findings": [],
        "review_required": False,
        "summary": "Photograph saved. Automatic assessment is unavailable, so the estimate is unchanged.",
        "changes_price": False,
    }


def failed_assessment() -> dict[str, Any]:
    return {
        "status": "failed",
        "findings": [],
        "review_required": False,
        "summary": "Photograph saved. Assessment did not finish, so the estimate is unchanged.",
        "changes_price": False,
    }


async def assess_image_bytes(image_bytes: bytes) -> dict[str, Any]:
    settings = get_settings()
    if not settings.openai_api_key:
        return unavailable_assessment()
    data_url = "data:image/jpeg;base64," + base64.b64encode(image_bytes).decode("ascii")
    payload = {
        "model": settings.openai_model,
        "messages": [
            {"role": "system", "content": _SYSTEM},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Assess this driveway photograph."},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            },
        ],
        "response_format": {"type": "json_object"},
    }
    try:
        async with httpx.AsyncClient(timeout=45) as client:
            res = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.openai_api_key}"},
                json=payload,
            )
            res.raise_for_status()
            body = res.json()
            content = body["choices"][0]["message"]["content"]
            parsed = json.loads(content)
    except Exception:
        logger.exception("driveway photograph assessment failed")
        return failed_assessment()
    result = interpret_findings(list(parsed.get("findings") or []))
    usage = body.get("usage") or {}
    result["prompt_tokens"] = int(usage.get("prompt_tokens") or 0)
    result["completion_tokens"] = int(usage.get("completion_tokens") or 0)
    return result
