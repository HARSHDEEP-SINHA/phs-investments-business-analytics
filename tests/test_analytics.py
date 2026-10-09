from backend.database import initialize_database
from backend.analytics import overview, monthly_trend, city_performance, scheme_performance, run_tool
from backend.agent import choose_tool, answer_question


def setup_module():
    initialize_database()


def test_overview_has_expected_fields():
    result = overview()
    assert result["synthetic_data"] is True
    assert result["inflows_inr"] > 0
    assert result["active_clients"] > 0
    assert result["net_flows_inr"] == round(result["inflows_inr"] - result["outflows_inr"], 2)


def test_monthly_trend_has_months():
    rows = monthly_trend()
    assert len(rows) >= 12
    assert all("month" in row and "net_flows_inr" in row for row in rows)


def test_limits_are_bounded():
    assert len(city_performance(1000)) <= 20
    assert len(scheme_performance(0)) == 1


def test_tool_allowlist_rejects_unknown_tool():
    try:
        run_tool("drop_tables")
        assert False, "Unknown tool should fail"
    except ValueError:
        pass


def test_question_routing():
    assert choose_tool("Which city has highest inflows?") == "city_performance"
    assert choose_tool("Summarize SIP registrations") == "sip_summary"
    assert choose_tool("Compare monthly trends") == "monthly_trend"


def test_chat_returns_grounded_result_without_api_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    result = answer_question("Give me a business overview")
    assert result["tool"] == "overview"
    assert result["facts"]["synthetic_data"] is True
    assert result["answer"]
