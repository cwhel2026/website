from app.routers.telegram import START_MESSAGE, _authorised_chat


def test_unauthorised_when_admin_list_empty(monkeypatch):
    from app.config import get_settings

    get_settings.cache_clear()
    monkeypatch.setenv("TELEGRAM_ADMIN_IDS", "")
    get_settings.cache_clear()
    assert not _authorised_chat(12345, 12345)


def test_authorised_when_user_in_list(monkeypatch):
    from app.config import get_settings

    get_settings.cache_clear()
    monkeypatch.setenv("TELEGRAM_ADMIN_IDS", "999888,111222")
    get_settings.cache_clear()
    assert _authorised_chat(999888, 999888)
    assert not _authorised_chat(123, 999888)
    assert not _authorised_chat(123, 555)


def test_start_message_defined():
    assert "SurfaceCoat" in START_MESSAGE

def test_business_report_empty_and_unknown():
    from app.routers.telegram import format_business_report
    report = format_business_report("COATING", {"jobs": [{"reference": "SC-1", "target_date": None}], "appointments": []})
    assert "SC-1" in report
    assert "target date: unknown" in report
    assert "None recorded" in report
    assert "Read-only report" in report
