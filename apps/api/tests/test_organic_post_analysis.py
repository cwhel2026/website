from app.services.marketing.organic_post_analysis import analyse_organic_caption


def test_detects_tarmac_angle():
    a = analyse_organic_caption("Fresh tarmac restoration in Preston — book a free quote")
    assert "tarmac_restoration" in a["angles"]
    assert a["location_hint"] == "Preston"


def test_flags_guarantee_claim():
    a = analyse_organic_caption("100% guaranteed cheapest driveway")
    assert "absolute_claim_review" in a["misleading_risk"]