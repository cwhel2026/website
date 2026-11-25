from app.services.finance.freeagent_reports import _extract_retained_profit


def test_extract_retained_profit_from_summary():
    pl = {"profit_and_loss_summary": {"retained_profit_carried_forward": "12345.67"}}
    assert _extract_retained_profit(pl) is not None
    assert float(_extract_retained_profit(pl)) == 12345.67


def test_extract_retained_profit_missing():
    assert _extract_retained_profit({}) is None