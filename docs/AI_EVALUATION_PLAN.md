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
