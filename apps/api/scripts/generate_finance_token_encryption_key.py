#!/usr/bin/env python3
"""Generate a FINANCE_TOKEN_ENCRYPTION_KEY value safe for token_vault (any string >= 16 chars).

Usage:
  python apps/api/scripts/generate_finance_token_encryption_key.py

Set the printed value as FINANCE_TOKEN_ENCRYPTION_KEY on the API service (not in chat).
"""

import secrets


def main() -> None:
    # URL-safe token; vault derives Fernet key via SHA-256 of this material — do not rotate without re-OAuth.
    print(secrets.token_urlsafe(48))


if __name__ == "__main__":
    main()