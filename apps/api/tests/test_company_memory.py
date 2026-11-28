from app.services.ai.company_memory import parse_memory


def test_memory_commands():
    assert parse_memory("/remember service_area = Lancashire") == ("service_area", "Lancashire")
    assert parse_memory("/forget service_area") == ("service_area", None)
    assert parse_memory("remember service_area = Lancashire") is None
    assert parse_memory("/remember invalid key = value") is None
    assert parse_memory("/remember note = " + "x" * 501) is None
