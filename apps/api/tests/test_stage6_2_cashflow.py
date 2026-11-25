from app.services.finance.freeagent_reports import _extract_retained_profit


def test_retained_profit_still_used():
    assert _extract_retained_profit({"profit_and_loss_summary": {"retained_profit_carried_forward": "100"}}) is not None