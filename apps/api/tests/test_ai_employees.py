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


def test_natural_greetings():
    assert route_employee("Hey Olivia where should we target?") == (("marketing",), "where should we target?")
    assert route_employee("Hi Arthur, cost this job") == (("finance",), "cost this job")


def test_shared_company_handbook():
    from app.services.ai.company_handbook import COMPANY_HANDBOOK
    assert "SurfaceCoat Ltd" in COMPANY_HANDBOOK
    assert "Marl Coatings" in COMPANY_HANDBOOK
    assert "owner approval" in COMPANY_HANDBOOK
