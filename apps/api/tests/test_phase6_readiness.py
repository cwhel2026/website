from app.services.marketing.integration_setup import _row
from app.services.marketing.launch_readiness import assess_launch_readiness


def test_credentials_do_not_verify_provider():
    row = _row("example", configured=True, live_read=True, live_write=True, env_vars=[], steps="")
    assert row["state"] == "configured_untested"
    assert not row["live_read_verified"]
    assert not row["live_write_verified"]


def test_unverified_required_items_block_launch():
    result = assess_launch_readiness()
    assert result["ready_score"] == 0
    for item in result["items"]:
        if not item["optional"]:
            assert item["label"] in result["external_blockers"]
