from app.services.territory_lookup import extract_outward_postcode


def test_extract_outward_postcode_standard():
    assert extract_outward_postcode("L39 4RX") == "L39"
    assert extract_outward_postcode("PR8 1AA") == "PR8"
    assert extract_outward_postcode("M1 1AE") == "M1"


def test_extract_outward_postcode_compact():
    assert extract_outward_postcode("L394RX") == "L39"


def test_extract_outward_postcode_invalid():
    assert extract_outward_postcode("not-a-postcode") is None