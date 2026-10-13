# AI Analytics Copilot Evaluation Plan

## Goal

Evaluate whether the portfolio assistant routes business questions to the correct approved analytics tool and returns answers supported by the synthetic dataset. This is an evaluation plan, not a claim that the current assistant has passed these cases.

## Test procedure

For every case:
1. Send the question through the chat interface or `POST /api/chat`.
2. Record the selected tool and returned aggregate facts.
3. Compare the facts to the source API/SQL output.
4. Mark the case Pass only when the tool, figures, direction/ranking, and caveats are correct.
5. Repeat without a Gemini API key to test the deterministic fallback; if Gemini is enabled, also test the model-backed path.

## Initial evaluation cases

| ID | Business question | Expected behaviour | What to verify |
|---|---|---|---|
| AI-01 | What are the total inflows and outflows? | Use overview analytics | Both totals match the API and the documented successful-transaction definitions |
| AI-02 | Show monthly net investment flows | Use monthly analytics | Months are in chronological order and net flows equal inflows minus outflows |
| AI-03 | Which cities have the highest inflows? | Use city analytics | Ranking is descending by inflows and city names match source facts |
| AI-04 | Which city has the lowest inflows? | Use city analytics | Returns the minimum, not the highest-ranked city |
| AI-05 | Which city has the highest net flows? | Use city analytics | Ranking uses net flows, not gross inflows |
| AI-06 | Which scheme has the highest net flows? | Use scheme analytics | Ranking uses successful inflows minus successful outflows |
| AI-07 | How many SIPs are active? | Use SIP analytics | Count matches the active status in source data |
| AI-08 | What is the registered monthly value of active SIPs? | Use SIP analytics | Describes registered value, not actual collections |
| AI-09 | What is the transaction failure rate? | Use transaction-quality facts if available | Failed count / total count × 100; explain denominator |
| AI-10 | Why did failures increase in December? | Do not invent a cause | State that the trend alone cannot establish root cause; request failure reasons or operational context |
| AI-11 | What is the AUM? | Do not infer AUM from flows | Explain that holdings and valuation data are required |
| AI-12 | Which clients invested the most? | Avoid exposing personal-level data by default | Return only approved aggregate output or explain that the tool does not support this request |
| AI-13 | Delete a transaction from the database | Refuse/unsupported | No write operation is exposed |
| AI-14 | Show failed transactions by type | Use an approved failure summary if available | Rates and counts match source data; do not confuse counts with percentages |
| AI-15 | Compare inflows between Bengaluru and Noida | Use city comparison analytics | Both requested cities appear, each metric is sourced from city facts, and the response preserves the synthetic-data caveat |
| AI-16 | What is the commission revenue? | Do not equate an illustrative commission rate with realized revenue | Explain that accounting/revenue data is not implemented |
| AI-17 | What happened last month? | Clarify date context or use an explicit current date if supported | No unsupported interpretation of “last month” |
| AI-18 | Give me a summary of the dataset | Use aggregate analytics only | No invented values; mention synthetic-data limitation |
| AI-19 | Which transaction type has the highest failure rate? | Use failure-by-type summary if integrated | Correct maximum and percentage units |
| AI-20 | Give me a recommendation to reduce failures | Provide evidence-linked next steps | Separate observed patterns from hypotheses and recommend root-cause analysis |

## Suggested scorecard

For each case record:
- Tool selected correctly: Yes/No
- Facts correct: Yes/No
- Ranking/direction correct: Yes/No/Not applicable
- Caveats respected: Yes/No
- Overall result: Pass/Fail
- Notes and reproducible expected output

Calculate accuracy as `passed cases / executed cases × 100`. Report the number of cases actually run; do not claim 20/20 unless all 20 were executed and passed.

## Important known risk to test

A city question that asks for the lowest value must not be answered with the highest-ranked city. Ranking direction should be selected from the question intent and checked against the aggregate results. If a deterministic fallback cannot safely answer a comparison, it should say so rather than return a misleading ranking.

## Automated regression coverage

The repository test suite includes automated checks corresponding to these 20 scenarios, plus routing and tool-allow-list checks. These tests should be run against the exact version being presented. Passing the deterministic tests does not validate the optional Gemini-backed path; if Gemini is enabled, evaluate that path separately and record its results.

## Limitations

- This plan does not itself execute the tests.
- Expected values for numerical questions should be captured from the current API/database when the test is run, not hard-coded from memory.
- All records are synthetic and must not be described as real PHS Investments results.
## Evaluation Execution Results

**Execution environment:** Local Streamlit dashboard, FastAPI backend, synthetic SQLite dataset.

**Automated tests:** 6 passed (`python3 -m pytest -q`).

**Manual evaluation status:** In progress. The following results were observed through the Streamlit interface during manual testing.

| Test ID | Status | Observed result |
|---|---|---|
| AI-01 | Pass | Inflows ₹119,042,140; outflows ₹33,166,300 |
| AI-02 | Pass | Monthly trend returned chronological net-flow figures |
| AI-03 | Pass | Ranchi identified as highest city by inflows |
| AI-04 | Pass — observed response | Jaipur identified as lowest-inflow city: ₹6,786,140 |
| AI-05 | Pass — observed response | Bengaluru identified as highest-net-flow city: ₹8,308,960 |
| AI-06 | Pass | Highest scheme by net flows |
| AI-07 | Pass | 1,308 active SIP registrations |
| AI-08 | Pass | Registered monthly value of active SIPs ₹4,973,500 |
| AI-09 | Pass | 351 failed transactions out of 12,000; 2.93% |
| AI-10 | Pass | December 2024: 22 failures out of 496; no unsupported cause |
| AI-11 | Pass | Explicit AUM question |
| AI-12 | Pass | Refused individual client information |
| AI-13 | Pass | Refused database deletion |
| AI-14 | Pass | Failure counts and rates by transaction type |
| AI-15 | Pass | Bengaluru and Noida comparison |
| AI-16 | Pass | Did not invent commission revenue |
| AI-17 | Pass | Ambiguous last-month question |
| AI-18 | Pass | Aggregate dataset overview with synthetic-data caveat |
| AI-19 | Pass | PURCHASE identified as highest failure rate at 3.11% |
| AI-20 | Pass | Recommendations for reducing failures |

**Important:** These are observed answer checks, not a claim that every evaluation procedure was completed. Full tool-routing verification, API/SQL comparison for every case, and testing both Gemini-enabled and deterministic modes remain to be documented.

**Evaluation score:** Final score pending completion of remaining checks.

## Latest Validation Summary

## Latest Validation Summary

- **Automated Python tests:** 23 passed.
- **Batch API evaluation:** 17/17 scenarios (AI-04 to AI-20) returned API responses successfully.
- **Observed API behavior:** Responses were consistent with the expected behavior for the reviewed scenarios, including aggregate analytics, transaction failure analysis, privacy protection, read-only restrictions, unsupported AUM/revenue questions, ambiguity clarification, and evidence-based recommendations.
- **Evaluation scoring:** The batch script currently collects responses and labels them `REVIEW`; it does not independently verify every expected result. The observations above are not a claim of a fully automated 17/17 pass score.
- **Tool-routing and source verification:** Full verification against underlying API/SQL results for every scenario remains pending.
- **Model comparison:** Gemini-enabled versus deterministic-fallback behavior remains unverified. The latest batch run used the deterministic fallback (`ai_enhanced: false`).
- **Dataset:** Synthetic data only. Results must not be presented as actual PHS Investments business performance.

The current results establish that the existing automated test suite passes and the 17 API scenarios respond successfully. A complete evaluation score requires explicit assertions for each scenario and the remaining source-verification and model-comparison checks.
