# Power BI report guide

This project uses synthetic mutual-fund distribution data for learning. Do not add real client data.

## 1. Generate local CSV exports

From the repository root, with the virtual environment activated:

```bash
python -m scripts.export_powerbi_data
```

The script initializes the local SQLite database if needed and writes files into `exports/`:
- `transactions.csv`: transaction-level synthetic fact table
- `clients.csv`: client dimension
- `schemes.csv`: scheme dimension
- `sips.csv`: SIP registration table
- `monthly_trend.csv`: month-level KPI table
- `city_performance.csv`: city-level KPI table
- `scheme_performance.csv`: scheme-level KPI table
- `sip_status_summary.csv`: SIP status aggregates
- `data_quality_report.json`: basic validation counts

Generated exports are ignored by Git. Do not commit generated datasets or any real customer data.

## 2. Power BI on macOS

Power BI Desktop is a Windows application. On a Mac, use one of these routes:
1. If you have access to a Windows PC or Windows virtual machine, install Power BI Desktop there and import the CSV files.
2. If your organization or account offers Power BI Service report creation in the browser, try importing the CSV files there; available authoring features depend on the account/workspace.
3. If neither is available, build the same BI report in Looker Studio or Tableau Public for now, then recreate it in Power BI when you have Windows access.

Do not spend time installing random unofficial Power BI Mac apps.

## 3. Recommended model

For a simple first report, import:
- `transactions.csv`
- `clients.csv`
- `schemes.csv`

Create one-to-many relationships:
- `clients[client_id]` (one) -> `transactions[client_id]` (many)
- `schemes[scheme_id]` (one) -> `transactions[scheme_id]` (many)

Use single-direction filtering from dimensions to transactions. Avoid connecting the aggregate CSVs to the transaction fact table in the first version; they are pre-aggregated alternatives for quick charts and can create double counting if combined carelessly.

The `sips.csv` table has its own grain (one row per SIP registration). It can be analyzed separately. Do not relate SIP registrations to transactions by client alone because that can multiply rows. The synthetic generator currently associates transaction SIP IDs independently of transaction client/scheme, so avoid using `sip_id` as a reliable cross-table relationship until that data-generation limitation is fixed.

## 4. Report layout

Create a one-page management overview:
- KPI cards: inflows, outflows, net flows, active clients, successful transactions, failed transactions
- Line chart: monthly inflows and outflows
- Bar chart: net flows by city
- Bar chart: inflows by scheme category or scheme
- Slicers: transaction date, city, scheme category, transaction status

Suggested base measures in DAX (assuming table names match the CSV names):

```dax
Successful Inflows =
CALCULATE (
    SUM ( transactions[amount_inr] ),
    transactions[transaction_status] = "Successful",
    transactions[transaction_type] IN { "PURCHASE", "SIP_INSTALLMENT", "SWITCH_IN" }
)

Successful Outflows =
CALCULATE (
    SUM ( transactions[amount_inr] ),
    transactions[transaction_status] = "Successful",
    transactions[transaction_type] IN { "REDEMPTION", "SWITCH_OUT" }
)

Net Flows = [Successful Inflows] - [Successful Outflows]

Successful Transactions =
CALCULATE (
    COUNTROWS ( transactions ),
    transactions[transaction_status] = "Successful"
)

Failed Transactions =
CALCULATE (
    COUNTROWS ( transactions ),
    transactions[transaction_status] = "Failed"
)
```

If Power BI rejects a comma/semicolon or table reference, verify your locale and the exact table names shown in the Fields pane.

## 5. Data quality and metric limitations

Open `data_quality_report.json` after export. Foreign-key violations, blank transaction IDs, negative amounts and duplicate transaction ID groups should all be zero.

- Inflows = successful PURCHASE, SIP_INSTALLMENT and SWITCH_IN transactions.
- Outflows = successful REDEMPTION and SWITCH_OUT transactions.
- Net flows = inflows minus outflows.
- These are transaction-flow metrics, not AUM, investment returns, realized commission revenue or client account balances.
- SIP registered monthly value is not actual SIP collections.
- All values and names are synthetic and must not be represented as real PHS Investments performance.
