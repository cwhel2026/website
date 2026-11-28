import re

def complete_excerpt(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    suffix = "\n[Summary shortened]"
    prefix = text[:max(0, limit - len(suffix))]
    boundaries = list(re.finditer(r"[.!?](?=\s|$)|\n", prefix))
    if boundaries:
        prefix = prefix[:boundaries[-1].end()]
    else:
        prefix = prefix.rsplit(" ", 1)[0] if " " in prefix else ""
    return prefix.rstrip() + suffix
