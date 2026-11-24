# Security

## Phase 7 (implemented)

- Passwords hashed with bcrypt.
- JWT secret from environment (`JWT_SECRET`); **production startup fails** on weak/default secrets.
- Production startup fails if default admin password is unchanged.
- Admin routes require bearer token with `owner` or `admin` role.
- Rate limits on public quote, login, and flyer lookup (per IP, in-memory).
- Security headers + `X-Request-ID` on API responses.

## Still before high-traffic production

- HTTPS only (platform responsibility).
- HTTP-only secure cookies instead of `localStorage` JWT (dashboard).
- CSRF if cookie auth is adopted.
- RBAC expansion beyond owner/admin.
- Audit log coverage for all admin mutations.
- Redis-backed rate limiting when API runs on multiple replicas.
- Disable or protect `/docs` on public API hosts.

Customer uploads and arbitrary HTML are not accepted (reduces attack surface).

See `INTEGRATIONS.md` for third-party credential status — nothing is “verified live” until recorded there.