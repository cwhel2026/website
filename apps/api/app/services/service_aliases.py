"""Map marketing / website service slugs to rows in the `services` table."""

from __future__ import annotations

# Website and quote wizard historically used short slugs; bootstrap uses longer catalogue slugs.
SERVICE_SLUG_ALIASES: dict[str, str] = {
    "tarmac-restoration": "tarmac-driveway-restoration",
    "block-paving": "block-paving-cleaning-sealing",
    "imprinted-concrete": "imprinted-concrete-restoration",
    "minor-repairs": "minor-tarmac-repairs",
    "commercial-car-parks": "commercial-car-park-restoration",
    "pressure-washing": "pressure-washing",
    "tarmac-recolouring": "tarmac-recolouring",
}


def resolve_service_slug(slug: str) -> str:
    key = slug.strip().lower()
    return SERVICE_SLUG_ALIASES.get(key, key)