# Security — Phase 1

- Passwords hashed with bcrypt.
- JWT secret from environment (`JWT_SECRET`); never commit secrets.
- Admin routes require bearer token with `owner` or `admin` role.
- Public quotation endpoint is intentionally unauthenticated; rate limiting planned Phase 7.
- Customer uploads and external HTML not yet accepted (reduces attack surface in Phase 1).

Before production: HTTPS only, secure cookies, CSRF on cookie auth, RBAC expansion, audit log for admin actions, secrets in Railway/platform vault.