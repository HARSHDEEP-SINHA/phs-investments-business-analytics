# Looker Studio / Data Studio Dashboard Build Checklist

All data in this portfolio project is synthetic. Do not upload real PHS Investments client or account data.

## Current local export files

Run from the repository root:

```bash
python -m scripts.export_powerbi_data
```

The script writes the `exports/` directory locally. Current useful report files include:

- `monthly_trend.csv` — monthly successful inflows, outflows, net flows, and successful/failed transaction counts
- `city_performance.csv` — aggregate investment flows and transacting clients by city
- `scheme_performance.csv` — aggregate flows by scheme
- `sip_status_summary.csv` — SIP registrations and registered monthly value by status
- `transaction_failure_by_type.csv` — transaction counts and failure rate by transaction type
- `monthly_failure_trend.csv` — monthly transaction counts and failure rate
- `data_quality_report.json` — local synthetic-data quality checks

## Main dashboard page

Recommended layout:
1. Three scorecards: Total Inflows, Total Outflows, Net Flows. Use INR currency formatting with zero decimal places.
2. Line chart: monthly inflows and outflows from `monthly_trend.csv`.
3. Line chart: monthly net flows from `monthly_trend.csv`.
4. Horizontal bar chart: net flows by city from `city_performance.csv`.
5. Horizontal bar chart: inflows by city from `city_performance.csv`.
6. Add scheme and SIP charts if there is enough room; otherwise put them on a separate page.

For scorecards, select the metric, open Style, enable comparison only if a meaningful comparison period is configured, and use a clear chart title. Avoid using a blended source unless the blend is needed and has a valid join key.

## Transaction Quality & Failures page

Add a new report page named **Transaction Quality & Failures**.

### Chart 1: Transaction Failure Rate by Type
Data source: `transaction_failure_by_type.csv`
- Chart: horizontal bar chart
- Dimension: `transaction_type`
- Metric: `failure_pct`
- Sort: `failure_pct`, descending
- Title: **Transaction Failure Rate by Type**
- Format `failure_pct` as a number with two decimal places and append a percent sign in the chart's display format if supported. Do not multiply by 100 again; the exported value is already a percentage.

### Chart 2: Monthly Failure Rate
Data source: `monthly_failure_trend.csv`
- Chart: line chart
- Dimension: `month`
- Metric: `failure_pct`
- Title: **Monthly Transaction Failure Rate**
- Format `failure_pct` as a percentage display only if the connector interprets values as fractions. The export stores values such as 3.11 to mean 3.11%, so prefer a numeric format with a percent suffix to avoid accidentally displaying 311%.

### Optional KPI scorecards
Use `monthly_failure_trend.csv` for:
- Total transactions: SUM of `total_transactions`
- Failed transactions: SUM of `failed_transactions`
- Average monthly failure rate: use AVG of `failure_pct` only when clearly labeled as an unweighted monthly average. For the overall failure rate, create a calculated field as `SUM(failed_transactions) / SUM(total_transactions) * 100` and label it **Overall Failure Rate (%)**.

## Connecting the data

Use the same connection method that successfully worked for the first dashboard source.

### If CSV upload works
Add each CSV as a separate data source. CSV uploads append rows to a dataset, so do not append a different schema to an existing dataset.

### If CSV upload is unavailable or fails
Use Google Sheets:
1. Open Google Sheets and create a workbook named **PHS Synthetic BI Exports**.
2. Import each CSV into its own worksheet using File → Import → Upload.
3. Keep each worksheet's header row and column types consistent.
4. In Data Studio, add a Google Sheets data source and select the corresponding worksheet.
5. Add the source to the report.

Use separate data sources for CSVs with different schemas. Don't blend sources unless you have a valid shared key and a clear reason to blend them.

## Validation before portfolio use

- All figures must be described as generated from synthetic data.
- Compare KPI totals to the Streamlit app and local exports.
- The quality report should show zero foreign-key violations, blank transaction IDs, negative amounts, and duplicate transaction-ID groups.
- Avoid claims about real clients, real assets under management, or actual business outcomes.
- Do not share the report publicly until its access settings and synthetic-data disclaimer are checked.
