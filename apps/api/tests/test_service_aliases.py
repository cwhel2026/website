from app.services.service_aliases import resolve_service_slug


def test_marketing_slugs_map_to_catalogue():
    assert resolve_service_slug("tarmac-restoration") == "tarmac-driveway-restoration"
    assert resolve_service_slug("block-paving") == "block-paving-cleaning-sealing"
    assert resolve_service_slug("tarmac-driveway-restoration") == "tarmac-driveway-restoration"