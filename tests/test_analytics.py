import pytest

from backend.database import initialize_database
from backend.analytics import (
    overview, monthly_trend, city_performance, scheme_performance,
    sip_summary, transaction_failures, run_tool,
)
from backend.agent import choose_tool, answer_question


@pytest.fixture(autouse=True)
def deterministic_mode(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    initialize_database()


def test_01_overview_has_consistent_kpis():
    result = overview()
    assert result["synthetic_data"] is True
    assert result["inflows_inr"] > 0
    assert result["outflows_inr"] >= 0
    assert result["net_flows_inr"] == round(result["inflows_inr"] - result["outflows_inr"], 2)
    assert result["active_clients"] > 0


def test_02_monthly_data_is_chronological_and_net_is_consistent():
    rows = monthly_trend()
    assert len(rows) >= 12
    assert [row["month"] for row in rows] == sorted(row["month"] for row in rows)
    assert all(row["net_flows_inr"] == round(row["inflows_inr"] - row["outflows_inr"], 2) for row in rows)


def test_03_city_limit_is_bounded():
    assert len(city_performance(1000)) <= 20


def test_04_lowest_city_inflows_returns_a_minimum():
    result = answer_question("Which city has the lowest inflows?")
    cities = result["facts"]["cities"]
    expected = min(cities, key=lambda row: row["inflows_inr"])
    assert result["tool"] == "city_performance"
    assert expected["city"] in result["answer"]
    assert "lowest" in result["answer"]


def test_05_highest_city_net_flows_uses_net_flows_metric():
    result = answer_question("Which city has the highest net flows?")
    expected = max(result["facts"]["cities"], key=lambda row: row["net_flows_inr"])
    assert expected["city"] in result["answer"]
    assert f"₹{expected['net_flows_inr']:,.0f}" in result["answer"]


def test_06_highest_scheme_net_flows_uses_all_schemes():
    result = answer_question("Which scheme has the highest net flows?")
    expected = max(result["facts"]["schemes"], key=lambda row: row["net_flows_inr"])
    assert expected["scheme_name"] in result["answer"]
    assert f"₹{expected['net_flows_inr']:,.0f}" in result["answer"]


def test_07_active_sip_count_matches_facts():
    result = answer_question("How many SIPs are active?")
    active = next(row for row in result["facts"]["statuses"] if row["status"].lower() == "active")
    assert result["tool"] == "sip_summary"
    assert f"{active['count']:,}" in result["answer"]


def test_08_active_sip_registered_value_is_not_called_collections():
    result = answer_question("What is the registered monthly value of active SIPs?")
    active = next(row for row in result["facts"]["statuses"] if row["status"].lower() == "active")
    assert f"₹{active['monthly_value_inr']:,.0f}" in result["answer"]
    assert "not actual monthly collections" in result["answer"]


def test_09_failure_rate_matches_numerator_and_denominator():
    result = transaction_failures()
    assert result["total_transactions"] > 0
    assert result["failed_transactions"] <= result["total_transactions"]
    assert result["failure_rate_pct"] == round(result["failed_transactions"] / result["total_transactions"] * 100, 2)
    assert result["synthetic_data"] is True


def test_10_december_question_does_not_invent_root_cause():
    result = answer_question("Why did failures increase in December?")
    assert result["tool"] == "transaction_failures"
    assert "does not identify the cause" in result["answer"]
    assert "error codes" in result["answer"].lower()


def test_11_aum_is_not_inferred_from_flows():
    result = answer_question("What is the AUM?")
    assert result["tool"] == "aum_guard"
    assert "cannot be determined" in result["answer"]
    assert "holdings and valuation" in result["answer"]


def test_12_personal_client_question_is_refused():
    result = answer_question("Which clients invested the most?")
    assert result["tool"] == "privacy_guard"
    assert "can't disclose personal" in result["answer"]


def test_13_database_write_request_is_refused():
    result = answer_question("Delete a transaction from the database")
    assert result["tool"] == "read_only_guard"
    assert "no records were changed" in result["answer"]


def test_14_failure_by_type_includes_counts_and_percentages():
    result = answer_question("Show failed transactions by type")
    facts = result["facts"]
    assert result["tool"] == "transaction_failures"
    assert f"{facts['failed_transactions']:,} of {facts['total_transactions']:,}" in result["answer"]
    for row in facts["by_type"]:
        assert row["transaction_type"] in result["answer"]
        assert f"{row['failure_rate_pct']:.2f}%" in result["answer"]


def test_15_city_comparison_returns_both_requested_cities():
    result = answer_question("Compare inflows between Bengaluru and Noida")
    assert result["tool"] == "city_comparison"
    assert "Bengaluru" in result["answer"]
    assert "Noida" in result["answer"]
    assert "net flows" in result["answer"]


def test_16_commission_revenue_is_not_inferred():
    result = answer_question("What is the commission revenue?")
    assert result["tool"] == "revenue_guard"
    assert "does not establish actual commission revenue" in result["answer"]


def test_17_ambiguous_last_month_question_asks_for_clarification():
    result = answer_question("What happened last month?")
    assert result["tool"] == "time_clarification"
    assert "previous calendar month" in result["answer"]
    assert "latest month available" in result["answer"]


def test_18_dataset_summary_uses_aggregate_facts_and_caveats():
    result = answer_question("Give me a summary of the dataset")
    assert result["tool"] == "overview"
    assert result["facts"]["synthetic_data"] is True
    assert "synthetic dataset" in result["answer"]
    assert "not assets under management" in result["answer"]


def test_19_highest_failure_rate_is_correctly_ranked():
    result = answer_question("Which transaction type has the highest failure rate?")
    expected = max(result["facts"]["by_type"], key=lambda row: row["failure_rate_pct"])
    assert expected["transaction_type"] in result["answer"]
    assert f"{expected['failure_rate_pct']:.2f}%" in result["answer"]


def test_20_failure_recommendations_separate_evidence_from_hypotheses():
    result = answer_question("Give me a recommendation to reduce failures")
    assert result["tool"] == "transaction_failures"
    assert "error codes" in result["answer"].lower()
    assert "not proven causes" in result["answer"]


def test_tool_allowlist_rejects_unknown_tool():
    with pytest.raises(ValueError, match="Unsupported analytics tool"):
        run_tool("drop_tables")


def test_routing_basics_and_deterministic_fallback():
    assert choose_tool("Which city has highest inflows?") == "city_performance"
    assert choose_tool("Summarize SIP registrations") == "sip_summary"
    assert choose_tool("Compare monthly trends") == "monthly_trend"
    result = answer_question("Give me a business overview")
    assert result["tool"] == "overview"
    assert result["facts"]["synthetic_data"] is True
    assert result["ai_enhanced"] is False
    assert result["answer"]
