"""Every API route must require authentication unless it is explicitly listed here.

Adding a public endpoint means adding it to PUBLIC_ROUTES with a reason, so the
change is visible in review.
"""

from app import auth
from app.main import app
from app.rate_limit import client_ip

PUBLIC_ROUTES = {
    # Sign-in / sign-out / owner recovery (setup-key gated, compare_digest, 5/min)
    ("POST", "/api/v1/auth/token"),
    ("POST", "/api/v1/auth/login"),
    ("POST", "/api/v1/auth/logout"),
    ("POST", "/api/v1/auth/owner/recover"),
    # Public website reads
    ("GET", "/api/v1/territories"),
    ("GET", "/api/v1/territories/{territory_id}"),
    ("GET", "/api/v1/services"),
    ("GET", "/api/v1/services/{slug}"),
    ("GET", "/api/v1/weather/forecast"),
    ("GET", "/api/v1/weather/status"),
    ("GET", "/api/v1/public/coverage"),
    ("GET", "/api/v1/marketing/flyer/{qr_slug}"),
    # Public website writes: the customer quote and enquiry forms (rate limited, idempotent submit)
    ("POST", "/api/v1/quotations/provisional"),
    ("POST", "/api/v1/quotations/submit"),
    ("POST", "/api/v1/public/commercial-enquiry"),
    ("POST", "/api/v1/marketing/attribution/track"),
    # Signed / shared-secret webhooks (fail closed when the secret is unset)
    ("POST", "/api/v1/telegram/webhook"),
    ("POST", "/api/v1/telegram/register-webhook/bootstrap"),
    ("GET", "/api/v1/marketing/webhooks/meta/leads"),
    ("POST", "/api/v1/marketing/webhooks/meta/leads"),
    ("GET", "/api/v1/marketing/webhooks/meta/feed"),
    ("POST", "/api/v1/marketing/webhooks/meta/feed"),
    ("POST", "/api/v1/marketing/webhooks/email/inbound"),
    ("POST", "/api/v1/finance/bookkeeping/receipts/telegram"),
    # OAuth redirect target, validated by the single-use state value
    ("GET", "/api/v1/finance/freeagent/callback"),
    # Probes
    ("GET", "/health"),
    ("GET", "/ready"),
}


def _dependency_calls(dependant, acc):
    for sub in dependant.dependencies:
        acc.add(sub.call)
        _dependency_calls(sub, acc)
    return acc


def test_every_route_is_authenticated_or_allowlisted():
    unauthenticated = set()
    for route in app.routes:
        if not hasattr(route, "dependant"):
            continue
        if auth.get_current_user in _dependency_calls(route.dependant, set()):
            continue
        for method in route.methods:
            unauthenticated.add((method, route.path))
    assert unauthenticated - PUBLIC_ROUTES == set(), "Unauthenticated routes not in allowlist"
    assert PUBLIC_ROUTES - unauthenticated == set(), "Allowlist entries that no longer exist or now require auth"


class _Req:
    def __init__(self, peer, xff=None):
        self.client = type("C", (), {"host": peer})()
        self.headers = {"x-forwarded-for": xff} if xff else {}


def test_rate_limit_key_uses_edge_address_only_behind_local_proxy():
    assert client_ip(_Req("127.0.0.1", "6.6.6.6, 203.0.113.9")) == "203.0.113.9"
    assert client_ip(_Req("198.51.100.4", "6.6.6.6")) == "198.51.100.4"
    assert client_ip(_Req("127.0.0.1")) == "127.0.0.1"
