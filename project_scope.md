# Project Scope

## Objective
Build an end-to-end portfolio-grade business intelligence application for a fictional mutual-fund distribution business, using synthetic records only.

## Business questions
- What are transaction inflows, outflows and net flows by month?
- Which cities and scheme categories contribute the highest transaction inflows?
- How many active clients and SIP registrations exist in the sample?
- What transaction failure patterns should an operations analyst investigate?
- Can a Gemini-powered assistant explain approved aggregate metrics without inventing facts?

## Deliverables
- Relational SQLite database and reproducible synthetic data.
- Fixed SQL analytics and documented KPI definitions.
- FastAPI backend with explicit read-only endpoints.
- Streamlit dashboard with charts and KPI cards.
- Optional Gemini-powered analytics assistant with tool allow-list and deterministic fallback.
- Tests, architecture diagram, learning guide and interview walkthrough.
- Future extension: Power BI dashboard and optional BigQuery / Google Cloud deployment.

## Data and safety
All records and figures are synthetic. No real PHS Investments customer, transaction, account or portfolio information is included. This is a learning demo, not financial advice or a production financial system.
