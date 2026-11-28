from app.services.ai.employees import allowed_tool, route_employee


def test_employee_routing():
    assert route_employee("Olivia, draft an advert") == (("marketing",), "draft an advert")
    assert route_employee("/arthur cash flow") == (("finance",), "cash flow")
    assert route_employee("Both, review our budget")[0] == ("marketing", "finance")
    assert route_employee("Olivia's work")[0] == ()
    assert route_employee("/today")[0] == ()


def test_employee_tool_isolation():
    assert allowed_tool("finance", "finance_cashflow")
    assert not allowed_tool("marketing", "finance_cashflow")
    assert not allowed_tool("finance", "marketing_content_calendar")
    for slug in ("finance", "marketing", "personal_assistant"):
        assert not allowed_tool(slug, "marketing_pause_all")
        assert not allowed_tool(slug, "marketing_director_proactive")
