# Learning guide: understand the project, don't just run it

## 1. What you are building
A small business-intelligence product with:
- **Database:** SQLite stores synthetic clients, schemes, SIP registrations and transactions.
- **Backend:** FastAPI exposes read-only metrics as HTTP endpoints.
- **Analytics layer:** fixed SQL queries calculate KPIs and rankings.
- **AI agent:** routes a question to an approved analytics function, then optionally asks Gemini to explain the returned JSON.
- **Frontend:** Streamlit displays KPIs, charts and a chat interface.

## 2. Run locally
Use Python 3.11 or 3.12.

```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn backend.main:app --reload
```

In a second terminal, activate the same environment and run:
```bash
streamlit run frontend/streamlit_app.py
```

Open the Streamlit URL printed in the terminal (usually http://localhost:8501). API docs are at http://127.0.0.1:8000/docs.

On Windows, if `cp` is unavailable, copy `.env.example` to `.env` manually.

## 3. Enable Gemini (optional)
1. Obtain a Gemini API key from an account you control and are authorized to use.
2. Put it in your local `.env` as `GEMINI_API_KEY=...`.
3. Never commit `.env`, API keys, credentials or real client data.
4. Restart the backend. Without a key, deterministic answers still work.

The selected model must be available to your account. API/model availability and billing can change; check your Google AI / Gemini API account settings.

## 4. Understand the request path
1. A user enters a question in Streamlit.
2. Streamlit sends JSON to FastAPI's `/api/chat`.
3. The agent routes the question to a fixed function such as `monthly_trend` or `city_performance`.
4. The function runs parameterized or fixed SQL against SQLite.
5. The facts are returned to the agent.
6. If configured, Gemini writes an explanation constrained to those facts. Otherwise a deterministic fallback is returned.
7. The API returns the answer, selected tool and facts for inspection.

## 5. Why the AI cannot run arbitrary SQL
Letting an LLM generate and execute unrestricted SQL creates security, correctness and cost risks. This demo uses an allow-list of read-only functions. A production design would add identity-aware authorization, query limits, auditing, monitoring, schema validation, and evaluation.

## 6. KPI definitions and caveats
- **Inflows:** successful PURCHASE, SIP_INSTALLMENT and SWITCH_IN transaction sums.
- **Outflows:** successful REDEMPTION and SWITCH_OUT transaction sums.
- **Net flows:** inflows minus outflows.
- **Active SIP monthly value:** sum of registered monthly amounts for active SIP records; it is not the value actually collected each month.
- **Transacting clients:** distinct clients with successful transactions.
- **Not calculated:** AUM, returns, profit, or actual commission revenue. Those require additional defensible data and definitions.

All records are synthetic. This project is educational and is not investment advice.

## 7. Exercises to prove understanding
1. Add a date filter to the monthly API without concatenating raw user input into SQL.
2. Add a category filter to the scheme table.
3. Add a query and test for transaction failure rate.
4. Write three additional SQL queries and explain their business use.
5. Ask Gemini the same five questions repeatedly and record unsupported claims or inconsistent answers.
6. Add an evaluation file with expected facts and pass/fail results.
7. Draw your own architecture diagram and explain every arrow in an interview.

## 8. Interview explanation
Explain the business problem first, then the data model, KPI definitions, SQL, dashboard, agent routing, grounding, security boundaries and limitations. Be transparent that the records are synthetic and distinguish completed functionality from future improvements.
