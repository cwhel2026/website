"""Rule-based post tagging for external creative — optional OpenAI vision later."""

from __future__ import annotations

import re

ANGLE_KEYWORDS = {
    "tarmac_restoration": ["tarmac", "asphalt", "resurface", "coating"],
    "block_paving": ["block", "paving", "bricks"],
    "before_after": ["before", "after", "transformation"],
    "commercial": ["car park", "commercial", "forecourt", "retail"],
    "offer": ["offer", "%", "discount", "free", "launch"],
    "local_awareness": ["preston", "lancashire", "local", "north west"],
    "replacement_alternative": ["replace", "restoration", "save", "instead of"],
}

CTA_KEYWORDS = ["quote", "quotation", "call", "message", "dm", "book", "enquir"]


def analyse_organic_caption(caption: str | None) -> dict:
    text = (caption or "").lower()
    angles = [k for k, words in ANGLE_KEYWORDS.items() if any(w in text for w in words)]
    services = []
    if "tarmac" in text or "asphalt" in text:
        services.append("tarmac_restoration")
    if "block" in text or "paving" in text:
        services.append("block_paving")
    if "wash" in text or "pressure" in text:
        services.append("pressure_washing")
    ctas = [w for w in CTA_KEYWORDS if w in text]
    headline_guess = None
    for line in (caption or "").split("\n"):
        line = line.strip()
        if 12 <= len(line) <= 90:
            headline_guess = line
            break
    location = "Preston" if "preston" in text else ("Lancashire" if "lancashire" in text else None)
    misleading_risk = []
    if re.search(r"\b100%\b|guaranteed|cheapest", text):
        misleading_risk.append("absolute_claim_review")
    if "before" in text and "after" in text and "example" not in text and "illustration" not in text:
        misleading_risk.append("confirm_customer_job_permission")
    return {
        "angles": angles,
        "services": services,
        "headline_guess": headline_guess,
        "offer_detected": "offer" in angles,
        "cta_tokens": ctas,
        "location_hint": location,
        "misleading_risk": misleading_risk,
        "analysis_mode": "rules",
    }