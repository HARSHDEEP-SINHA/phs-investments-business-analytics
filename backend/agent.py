"""Small analytics agent using a safe tool allow-list and optional Gemini explanations."""
from __future__ import annotations

import json
import os
from typing import Any

from .analytics import run_tool

SYSTEM_RULES = """You are an analytics assistant for a fictional mutual-fund distributor.
Only use the supplied JSON facts. Do not invent figures, causes, forecasts, investment advice, or sources.
State that the dataset is synthetic when relevant. Explain that inflows and net flows are transaction-based proxies,
not assets under management or actual accounting revenue. If the evidence does not explain a cause, say so.
Never request personal client data. Keep answers concise and show the most relevant numbers."""


def choose_tool(question: str) -> str:
    q = question.lower()
    if any(k in q for k in ["sip", "systematic investment"]):
        return "sip_summary"
    if any(k in q for k in ["city", "cities", "location", "region"]):
        return "city_performance"
    if any(k in q for k in ["scheme", "fund", "category", "redemption ratio"]):
        return "scheme_performance"
    if any(k in q for k in ["month", "monthly", "quarter", "trend", "over time", "compare period"]):
        return "monthly_trend"
    return "overview"


def deterministic_answer(question: str, tool_name: str, facts: dict[str, Any]) -> str:
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
                "This comparison alone does not establish why the figures changed.")
    if tool_name == "city_performance":
        cities = facts.get("cities", [])
        if not cities:
            return "No city-level results were returned."
        top = cities[0]
        return f"{top['city']} has the highest recorded inflows in the returned city ranking (₹{top['inflows_inr']:,.0f}). This is synthetic data, not a real business result."
    if tool_name == "scheme_performance":
        schemes = facts.get("schemes", [])
        if not schemes:
            return "No scheme-level results were returned."
        top = schemes[0]
        return f"{top['scheme_name']} ({top['category']}) ranks first by recorded inflows in this sample at ₹{top['inflows_inr']:,.0f}. This is not an investment recommendation."
    statuses = facts.get("statuses", [])
    return "SIP status summary: " + "; ".join(
        f"{r['status']}: {r['count']} registrations, ₹{r['monthly_value_inr']:,.0f} monthly registered value"
        for r in statuses
    ) + ". All records are synthetic."


def answer_question(question: str) -> dict:
    if not question or len(question.strip()) < 3:
        return {"answer": "Ask a business question with a little more detail.", "tool": None, "ai_enhanced": False}
    question = question.strip()[:1000]
    tool_name = choose_tool(question)
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
    except Exception as exc:
        # Do not expose exception details, API keys, or environment values to the UI.
        return {"answer": fallback, "tool": tool_name, "facts": facts, "ai_enhanced": False,
                "note": "Gemini was unavailable; returned a deterministic answer instead."}
