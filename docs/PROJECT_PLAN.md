# Project roadmap

## MVP (implemented in repository)
- [x] Synthetic SQLite data and relational schema
- [x] Fixed read-only SQL analytics functions
- [x] FastAPI endpoints
- [x] Streamlit dashboard and charts
- [x] AI question router with optional Gemini explanation
- [x] Deterministic fallback if Gemini is not configured
- [x] Basic tests and SQL examples
- [x] Learning guide and architecture notes

## Next milestones
1. Run the app locally and confirm tests pass.
2. Add a Power BI report using the same synthetic data or exported aggregate CSVs.
3. Add date-range filters and a category filter with validation.
4. Add an evaluation set of at least 20 natural-language questions with expected tool and facts.
5. Add authentication before any public deployment.
6. Optional: replace SQLite with BigQuery and configure an appropriately scoped Google Cloud identity.
7. Optional: deploy backend and frontend using separate services, secret storage, logging and budget alerts.

## Definition of done
- A fresh clone can be installed from README instructions.
- Synthetic data is created automatically on first API startup.
- Dashboard renders KPIs and charts.
- Chat answers with the chosen tool and inspectable facts.
- Tests pass.
- No real client records, credentials or API keys are in the repository.
