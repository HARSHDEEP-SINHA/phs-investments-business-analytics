"""Read-only analytics question router with deterministic, evidence-grounded responses."""
from __future__ import annotations

import json
import os
import re
from typing import Any

from dotenv import load_dotenv

load_dotenv()

from .analytics import run_tool

SYSTEM_RULES = """You are an analytics assistant for a fictional mutual-fund distributor.
Use only the supplied JSON facts. Never invent figures, causes, forecasts, investment advice, or sources.
All records are synthetic. Transaction inflows and net flows are not AUM or accounting revenue.
If the evidence does not establish a cause, say so. Never disclose individual client details.
Never claim to modify records. Keep answers concise and distinguish observations from hypotheses."""


def choose_tool(question: str) -> str:
    q = question.lower()
    # Safety/unsupported-intent routing must run before ordinary analytics routing.
    if any(k in q for k in ["assets under management", "aum"]):
        return "aum_guard"
    if any(k in q for k in ["commission revenue", "actual revenue", "recognized revenue", "accounting revenue"]):
        return "revenue_guard"
    if any(k in q for k in ["delete ", "remove ", "insert ", "update ", "modify ", "edit ", "drop table", "truncate table", "write to database", "update the database", "modify database", "change a transaction"]):
        return "read_only_guard"
    if any(k in q for k in ["which clients", "client names", "individual client", "personal client", "who invested", "client details"]):
        return "privacy_guard"
    if "last month" in q and not any(m in q for m in ["december 2025", "november 2025", "october 2025", "2025-12", "2025-11"]):
        return "time_clarification"
    if any(k in q for k in ["failure", "failed transaction", "transaction failed", "failure rate", "failures"]):
        return "transaction_failures"
    if any(k in q for k in ["compare", "comparison", "versus", " vs "]):
        if any(k in q for k in ["city", "cities", "location", "region", "inflows between", "bengaluru", "noida", "ranchi", "delhi"]):
            return "city_comparison"
        if any(k in q for k in ["month", "monthly", "period", "trend"]):
            return "monthly_trend"
    if any(k in q for k in ["sip", "systematic investment"]):
        return "sip_summary"
    if any(k in q for k in ["scheme", "fund", "category", "redemption ratio"]):
        return "scheme_performance"
    if any(k in q for k in ["city", "cities", "location", "region"]):
        return "city_performance"
    if any(k in q for k in ["month", "monthly", "quarter", "trend", "over time", "period"]):
        return "monthly_trend"
    return "overview"


def deterministic_answer(question: str, tool_name: str, facts: dict[str, Any]) -> str:
    q = question.lower()
    if tool_name == "aum_guard":
        return "AUM cannot be determined from this synthetic dataset. Transaction inflows and net flows are not assets under management. Holdings and valuation data would be required."
    if tool_name == "revenue_guard":
        return "The available synthetic dataset does not establish actual commission revenue. Transaction inflows and net flows are not commission income. Commission rates, fee records, and accounting data would be needed to calculate actual revenue."
    if tool_name == "privacy_guard":
        return "I can't disclose personal or individual client details. This demo supports aggregate, read-only analytics only. I can provide anonymized summaries or aggregate transaction statistics instead. All data in this demo is synthetic."
    if tool_name == "read_only_guard":
        return "I can't delete or modify database records. This application supports read-only analytics only, and no records were changed. You can ask me to summarize failed transactions instead. All data in this demo is synthetic."
    if tool_name == "time_clarification":
        return "Do you mean the previous calendar month or the latest month available in the dataset? The dataset runs from January 2024 through December 2025. All data is synthetic."
    if tool_name == "overview":
        return (f"From the synthetic dataset, successful transaction inflows total ₹{facts['inflows_inr']:,.0f}, "
                f"outflows total ₹{facts['outflows_inr']:,.0f}, and net flows are ₹{facts['net_flows_inr']:,.0f}. "
                f"There are {facts['active_clients']:,} active clients and {facts['active_sips']:,} active SIP registrations. "
                "These are transaction-based metrics, not assets under management or actual accounting revenue.")
    if tool_name == "monthly_trend":
        months = facts.get("months", [])
        if len(months) < 2:
            return "There is not enough monthly data to compare periods."
        first, last = months[0], months[-1]
        return (f"The available data runs from {first['month']} to {last['month']}. "
                f"Net flows were ₹{first['net_flows_inr']:,.0f} in the first month and ₹{last['net_flows_inr']:,.0f} in the last month. "
                "This comparison alone does not establish why the figures changed. All data is synthetic.")
    if tool_name in ("city_performance", "city_comparison"):
        cities = facts.get("cities", [])
        if not cities:
            return "No city-level results were returned."
        if tool_name == "city_comparison":
            known = {c["city"].lower(): c for c in cities}
            aliases = {"bengaluru": "bengaluru", "bangalore": "bengaluru", "noida": "noida",
                       "ranchi": "ranchi", "delhi": "delhi", "mumbai": "mumbai",
                       "pune": "pune", "jaipur": "jaipur", "gurugram": "gurugram",
                       "hyderabad": "hyderabad", "kolkata": "kolkata", "chennai": "chennai",
                       "lucknow": "lucknow"}
            requested = []
            for alias, canonical in aliases.items():
                if re.search(r"\b" + re.escape(alias) + r"\b", q) and canonical in known and canonical not in requested:
                    requested.append(canonical)
            if len(requested) < 2:
                return "Which two cities would you like to compare? I can compare their synthetic inflows, outflows, and net flows."
            lines = []
            for city_name in requested[:2]:
                city = known[city_name]
                lines.append(f"{city['city']}: inflows ₹{city['inflows_inr']:,.0f}, outflows ₹{city['outflows_inr']:,.0f}, net flows ₹{city['net_flows_inr']:,.0f}")
            return "City comparison from the synthetic dataset: " + "; ".join(lines) + ". These transaction-based metrics are not AUM or accounting revenue."
        if any(k in q for k in ["lowest", "least", "minimum", "smallest"]):
            metric = "net_flows_inr" if "net flow" in q else "inflows_inr"
            chosen = min(cities, key=lambda c: c[metric])
            metric_name = "net flows" if metric == "net_flows_inr" else "inflows"
            return f"{chosen['city']} has the lowest recorded {metric_name} in the returned sample at ₹{chosen[metric]:,.0f}. This is synthetic data, not a business result."
        metric = "net_flows_inr" if "net flow" in q else "inflows_inr"
        chosen = max(cities, key=lambda c: c[metric])
        metric_name = "net flows" if metric == "net_flows_inr" else "inflows"
        if any(k in q for k in ["highest", "top", "most", "maximum", "largest"]):
            return f"{chosen['city']} has the highest recorded {metric_name} in the returned sample at ₹{chosen[metric]:,.0f}. This is synthetic data, not a business result."
        return "City performance is available as aggregate synthetic data. Ask for the highest or lowest inflows/net flows, or name two cities to compare."
    if tool_name == "scheme_performance":
        schemes = facts.get("schemes", [])
        if not schemes:
            return "No scheme-level results were returned."
        metric = "net_flows_inr" if "net flow" in q else "inflows_inr"
        if any(k in q for k in ["lowest", "least", "minimum", "smallest"]):
            chosen = min(schemes, key=lambda s: s[metric])
            direction = "lowest"
        else:
            chosen = max(schemes, key=lambda s: s[metric])
            direction = "highest"
        metric_name = "net flows" if metric == "net_flows_inr" else "inflows"
        return f"{chosen['scheme_name']} ({chosen['category']}) has the {direction} recorded {metric_name} in this sample at ₹{chosen[metric]:,.0f}. This is synthetic data, not an investment recommendation."
    if tool_name == "transaction_failures":
        total = facts.get("total_transactions", 0)
        failed = facts.get("failed_transactions", 0)
        rate = facts.get("failure_rate_pct", 0)
        by_type = facts.get("by_type", [])
        monthly = facts.get("monthly", [])
        if "why" in q and "december" in q:
            dec = next((m for m in monthly if m["month"] == "2024-12"), None)
            if dec:
                return (f"In December 2024, {dec['failed_transactions']} of {dec['total_transactions']} transactions failed, "
                        f"a failure rate of {dec['failure_rate_pct']:.2f}%. The available data shows the failure rate, but does not identify the cause of the failures. "
                        "Error codes or payment-system logs would be needed. This is synthetic data.")
        if "by type" in q or "transaction type" in q or "highest failure rate" in q or "highest observed failure" in q:
            if not by_type:
                return "No failure-by-type data was returned."
            lines = [f"{r['transaction_type']}: {r['failure_rate_pct']:.2f}% ({r['failed_transactions']} failures out of {r['total_transactions']} transactions)" for r in by_type]
            highest = max(by_type, key=lambda r: r["failure_rate_pct"])
            return (f"From the synthetic dataset, {failed:,} of {total:,} transactions failed, giving an overall failure rate of {rate:.2f}%. "
                    + "By type: " + "; ".join(lines) + f". The highest failure rate is {highest['transaction_type']} at {highest['failure_rate_pct']:.2f}%. These are synthetic data, not real business results.")
        if any(k in q for k in ["recommend", "reduce", "improve", "prevent"]):
            highest = max(by_type, key=lambda r: r["failure_rate_pct"]) if by_type else None
            lead = f"The synthetic dataset shows {failed:,} failed transactions out of {total:,} ({rate:.2f}%). "
            if highest:
                lead += f"{highest['transaction_type']} has the highest observed failure rate at {highest['failure_rate_pct']:.2f}%. "
            return lead + "Recommendations: investigate error codes and payment-system logs; compare failure reasons across transaction types; check whether failures cluster by time or system; and monitor failure rates after corrective changes. These are investigation steps, not proven causes."
        return f"From the synthetic dataset, {failed:,} of {total:,} transactions failed, giving an overall failure rate of {rate:.2f}%. These are synthetic data, not real business results."
    statuses = facts.get("statuses", [])
    if tool_name == "sip_summary":
        active = next((r for r in statuses if r["status"].lower() == "active"), None)
        if active and any(k in q for k in ["how many", "count", "number"]):
            return f"There are {active['count']:,} active SIP registrations in the synthetic dataset. This is a registration count, not proof of actual collections."
        if active and any(k in q for k in ["monthly value", "registered value", "monthly amount"]):
            return f"Active SIP registrations have a combined registered monthly value of ₹{active['monthly_value_inr']:,.0f}. This is registered value, not actual monthly collections. All records are synthetic."
        return "SIP status summary: " + "; ".join(
            f"{r['status']}: {r['count']} registrations, ₹{r['monthly_value_inr']:,.0f} monthly registered value"
            for r in statuses
        ) + ". All records are synthetic."
    return "I couldn't safely answer that from the available aggregate data."


def answer_question(question: str) -> dict:
    if not question or len(question.strip()) < 3:
        return {"answer": "Ask a business question with a little more detail.", "tool": None, "facts": {}, "ai_enhanced": False}
    question = question.strip()[:1000]
    tool_name = choose_tool(question)
    if tool_name in ("aum_guard", "revenue_guard", "privacy_guard", "read_only_guard", "time_clarification"):
        return {"answer": deterministic_answer(question, tool_name, {}), "tool": tool_name, "facts": {}, "ai_enhanced": False}
    facts = run_tool(tool_name)
    fallback = deterministic_answer(question, tool_name, facts)

    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        return {"answer": fallback, "tool": tool_name, "facts": facts, "ai_enhanced": False,
                "note": "Set GEMINI_API_KEY in .env to enable Gemini-generated explanations."}
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        prompt = (SYSTEM_RULES + "\nUser question: " + question +
                  "\nSelected tool: " + tool_name + "\nTool result JSON: " +
                  json.dumps(facts, ensure_ascii=False) +
                  "\nWrite a concise answer grounded only in the JSON. Mention important limitations.")
        response = client.models.generate_content(model=model, contents=prompt)
        text = (response.text or "").strip()
        if not text:
            raise RuntimeError("Gemini returned an empty response")
        return {"answer": text, "tool": tool_name, "facts": facts, "ai_enhanced": True}
    except Exception:
        return {"answer": fallback, "tool": tool_name, "facts": facts, "ai_enhanced": False,
                "note": "Gemini was unavailable; returned a deterministic answer instead."}
