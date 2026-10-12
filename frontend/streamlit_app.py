"""Streamlit frontend for PHS Investments synthetic analytics demo."""
import os

import pandas as pd
import plotly.express as px
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()
API = os.getenv("API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
st.set_page_config(page_title="PHS | Business Intelligence", page_icon="📊", layout="wide")


@st.cache_data(ttl=30)
def get_json(path: str):
    response = requests.get(f"{API}{path}", timeout=10)
    response.raise_for_status()
    return response.json()


st.title("PHS Investments | Business Intelligence")
st.caption("Portfolio demonstration • Synthetic data only • Not financial or investment advice")

try:
    overview = get_json("/api/overview")
    monthly = get_json("/api/monthly")["months"]
    cities = get_json("/api/cities")["cities"]
    schemes = get_json("/api/schemes")["schemes"]
    sips = get_json("/api/sips")
    failures = get_json("/api/failures")
except requests.RequestException:
    st.error("Cannot reach the API. Start FastAPI first: uvicorn backend.main:app --reload")
    st.stop()

if overview.get("synthetic_data"):
    st.info("This dashboard uses reproducible synthetic records. Figures do not represent real clients, AUM or accounting revenue.")

def inr(value):
    return f"₹{value/100000:.2f}L"

k1, k2, k3, k4 = st.columns(4)
k1.metric("Transaction inflows", inr(overview["inflows_inr"]))
k2.metric("Transaction outflows", inr(overview["outflows_inr"]))
k3.metric("Net flows", inr(overview["net_flows_inr"]))
k4.metric("Active clients", f"{overview['active_clients']:,}")

k5, k6, k7 = st.columns(3)
k5.metric("Active SIP registrations", f"{overview['active_sips']:,}")
k6.metric("Successful transactions", f"{overview['successful_transactions']:,}")
k7.metric("Failed transactions", f"{overview['failed_transactions']:,}")

st.subheader("Monthly transaction flows")
df = pd.DataFrame(monthly)
if not df.empty:
    chart_df = df.melt(id_vars="month", value_vars=["inflows_inr", "outflows_inr"],
                       var_name="flow_type", value_name="amount_inr")
    fig = px.line(chart_df, x="month", y="amount_inr", color="flow_type", markers=True,
                  labels={"month":"Month", "amount_inr":"Amount (INR)", "flow_type":"Flow"})
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(df, use_container_width=True, hide_index=True)

left, right = st.columns(2)
with left:
    st.subheader("Cities by inflows")
    city_df = pd.DataFrame(cities)
    if not city_df.empty:
        st.plotly_chart(px.bar(city_df, x="city", y="inflows_inr", title="Synthetic inflows by city"),
                        use_container_width=True)
with right:
    st.subheader("Schemes by inflows")
    scheme_df = pd.DataFrame(schemes)
    if not scheme_df.empty:
        st.plotly_chart(px.bar(scheme_df.head(8), x="scheme_name", y="inflows_inr", color="category",
                               title="Top schemes by synthetic inflows"),
                        use_container_width=True)

st.subheader("SIP status")
sip_df = pd.DataFrame(sips["statuses"])
st.dataframe(sip_df, use_container_width=True, hide_index=True)

st.subheader("Transaction quality")
failure_types = pd.DataFrame(failures.get("by_type", []))
monthly_failures = pd.DataFrame(failures.get("monthly", []))
if not failure_types.empty:
    failure_types = failure_types.sort_values("failure_rate_pct", ascending=False)
    st.plotly_chart(
        px.bar(failure_types, x="transaction_type", y="failure_rate_pct",
               title="Failure rate by transaction type",
               labels={"transaction_type": "Transaction type", "failure_rate_pct": "Failure rate (%)"}),
        use_container_width=True,
    )
if not monthly_failures.empty:
    st.plotly_chart(
        px.line(monthly_failures, x="month", y="failure_rate_pct", markers=True,
                title="Monthly transaction failure rate",
                labels={"month": "Month", "failure_rate_pct": "Failure rate (%)"}),
        use_container_width=True,
    )
st.caption(
    f"Overall synthetic failure rate: {failures.get('failure_rate_pct', 0):.2f}% "
    f"({failures.get('failed_transactions', 0):,} failed of "
    f"{failures.get('total_transactions', 0):,} transactions). Rates describe the data; they do not identify root causes."
)

st.divider()
st.header("Ask the Analytics Agent")
st.write("Ask about overview KPIs, monthly trends, city or scheme rankings, SIP registrations, transaction failures, or a comparison between two cities. The assistant uses approved read-only analytics tools.")
examples = [
    "Give me an overview of business performance",
    "Compare the monthly trends",
    "Which cities have the highest inflows?",
    "Summarize SIP registrations",
    "Which schemes have the highest inflows?",
    "Compare inflows between Bengaluru and Noida",
    "Show failed transactions by type",
    "Which transaction type has the highest failure rate?",
]
selected = st.selectbox("Example question", ["Choose a question..."] + examples)
question = st.text_input("Your question", value="" if selected == "Choose a question..." else selected,
                         placeholder="e.g. Which cities have the highest inflows?")
if st.button("Ask agent", type="primary") and question.strip():
    try:
        with st.spinner("Querying approved analytics tools..."):
            response = requests.post(f"{API}/api/chat", json={"question": question}, timeout=45)
            response.raise_for_status()
            result = response.json()
        st.markdown(result["answer"])
        st.caption(f"Tool: {result.get('tool') or 'none'} • Gemini-generated: {'Yes' if result.get('ai_enhanced') else 'No'}")
        if result.get("note"):
            st.info(result["note"])
        with st.expander("Inspect evidence returned by the analytics tool"):
            st.json(result.get("facts", {}))
    except requests.RequestException:
        st.error("The agent API could not complete the request. Check that the backend is running.")

with st.expander("How to interpret this demo"):
    st.markdown("""
    - **Inflows/outflows** are transaction-type sums from successful synthetic records.
    - **Net flows** = inflows − outflows; this is not AUM or investment performance.
    - Commission revenue is not reported because this demo does not model actual fee accruals.
    - The agent uses a fixed tool allow-list and does not execute arbitrary SQL generated by the model.
    """)
