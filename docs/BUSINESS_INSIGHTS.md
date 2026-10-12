# Business Insights & Recommendations

> **Data disclaimer:** This portfolio analysis uses entirely synthetic data generated for demonstration. The figures below are not actual PHS Investments client, transaction, or business results and must not be presented as real company performance.

## Executive summary

The demonstration dataset contains **12,000 transactions** across January 2024–December 2025. The exported monthly quality summary records **351 failed transactions**, equivalent to an overall failure rate of **2.93%** (351 / 12,000, rounded to two decimal places).

## Key findings

1. **Purchase transactions have the highest observed failure rate by transaction type.** The synthetic summary reports a **3.11%** failure rate for PURCHASE, followed by **SIP_INSTALLMENT at 3.05%**. REDEMPTION is **2.84%**, SWITCH_OUT is **2.52%**, and SWITCH_IN is **1.34%**.
2. **Failure rates vary month to month.** In the synthetic monthly summary, the rate ranges from **1.43% (November 2024)** to **4.44% (December 2024)**. This variation suggests that a monthly trend view is useful for identifying periods that warrant further investigation.
3. **The aggregate failure rate is a starting point, not a diagnosis.** These summaries show where failures are more frequent, but do not establish why they occurred. Root causes would require additional fields such as payment method, error code, bank response, retry outcome, or processing channel.

## Recommended next steps

- **Prioritise purchase and SIP-installment failures:** review failed records for these transaction types first, then group them by available failure reason or processing channel.
- **Investigate monthly spikes:** compare high-failure months with transaction volumes and operational events before drawing conclusions.
- **Track both counts and rates:** a high failure count can result from high transaction volume; rate and count should be reviewed together.
- **Monitor recovery:** if retry data becomes available, measure how many failed transactions later succeed and how long recovery takes.
- **Create an operational alert threshold:** establish a threshold with business stakeholders and alert when the failure rate exceeds it for a defined period.
- **Validate data regularly:** retain checks for blank or duplicate transaction IDs, negative amounts, and foreign-key violations before refreshing reports.

## Metric definitions

- **Failure rate by transaction type** = failed transactions of that type / all transactions of that type × 100.
- **Overall failure rate** = total failed transactions / total transactions × 100.
- **Monthly failure rate** = failed transactions in a month / all transactions in that month × 100.
- **Net investment flows** = successful inflows minus successful outflows, using the transaction-type rules documented in the project SQL.

The dashboard's average of monthly failure percentages is an unweighted average of monthly rates. It can differ from the overall failure rate because months may contain different transaction volumes.

## Interview talking point

“I built a synthetic investment analytics project that combines a Python/SQLite data model, SQL aggregations, automated CSV exports, and a Looker Studio dashboard. I used the report to compare transaction failure rates by type and month, validate KPI totals, and turn descriptive findings into investigation steps. The dataset is synthetic, so the results demonstrate my analytics workflow rather than real business outcomes.”
