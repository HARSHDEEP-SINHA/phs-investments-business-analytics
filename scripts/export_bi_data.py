"""Export synthetic SQLite tables and curated aggregates for BI tools.

Run from the repository root:
    python -m scripts.export_bi_data
All exported files contain synthetic portfolio-demo data only.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from backend.database import ROOT, connect, initialize_database

EXPORT_DIR = ROOT / "data" / "exports"


def export_query(conn, filename: str, query: str) -> int:
    frame = pd.read_sql_query(query, conn)
    frame.to_csv(EXPORT_DIR / filename, index=False)
    return len(frame)


def main() -> None:
    initialize_database()
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    counts: dict[str, int] = {}

    with connect() as conn:
        counts["clients.csv"] = export_query(
            conn, "clients.csv",
            """SELECT client_id, city, client_segment, acquisition_channel,
                      join_date, client_status
               FROM clients ORDER BY client_id""",
        )
        counts["schemes.csv"] = export_query(
            conn, "schemes.csv",
            """SELECT scheme_id, scheme_name, amc_name, category, risk_level,
                      illustrative_commission_rate
               FROM schemes ORDER BY scheme_id""",
        )
        counts["sips.csv"] = export_query(
            conn, "sips.csv",
            """SELECT sip_id, client_id, scheme_id, monthly_amount, start_date, sip_status
               FROM sips ORDER BY sip_id""",
        )
        counts["transactions.csv"] = export_query(
            conn, "transactions.csv",
            """SELECT transaction_id, client_id, scheme_id, sip_id, transaction_date,
                      transaction_type, amount_inr, transaction_status
               FROM transactions ORDER BY transaction_date, transaction_id""",
        )
        counts["monthly_summary.csv"] = export_query(
            conn, "monthly_summary.csv",
            """SELECT substr(transaction_date, 1, 7) AS month,
                      SUM(CASE WHEN transaction_type IN ('PURCHASE','SIP_INSTALLMENT','SWITCH_IN')
                               THEN amount_inr ELSE 0 END) AS inflows_inr,
                      SUM(CASE WHEN transaction_type IN ('REDEMPTION','SWITCH_OUT')
                               THEN amount_inr ELSE 0 END) AS outflows_inr,
                      COUNT(*) AS successful_transaction_count
               FROM transactions
               WHERE transaction_status='Successful'
               GROUP BY substr(transaction_date, 1, 7)
               ORDER BY month""",
        )
        counts["city_summary.csv"] = export_query(
            conn, "city_summary.csv",
            """SELECT c.city,
                      SUM(CASE WHEN t.transaction_type IN ('PURCHASE','SIP_INSTALLMENT','SWITCH_IN')
                               THEN t.amount_inr ELSE 0 END) AS inflows_inr,
                      SUM(CASE WHEN t.transaction_type IN ('REDEMPTION','SWITCH_OUT')
                               THEN t.amount_inr ELSE 0 END) AS outflows_inr,
                      COUNT(DISTINCT t.client_id) AS transacting_clients
               FROM transactions t JOIN clients c ON c.client_id=t.client_id
               WHERE t.transaction_status='Successful'
               GROUP BY c.city ORDER BY inflows_inr DESC""",
        )
        counts["scheme_summary.csv"] = export_query(
            conn, "scheme_summary.csv",
            """SELECT s.scheme_id, s.scheme_name, s.category,
                      SUM(CASE WHEN t.transaction_type IN ('PURCHASE','SIP_INSTALLMENT','SWITCH_IN')
                               THEN t.amount_inr ELSE 0 END) AS inflows_inr,
                      SUM(CASE WHEN t.transaction_type IN ('REDEMPTION','SWITCH_OUT')
                               THEN t.amount_inr ELSE 0 END) AS outflows_inr,
                      COUNT(*) AS successful_transactions
               FROM transactions t JOIN schemes s ON s.scheme_id=t.scheme_id
               WHERE t.transaction_status='Successful'
               GROUP BY s.scheme_id, s.scheme_name, s.category
               ORDER BY inflows_inr DESC""",
        )
        counts["sip_summary.csv"] = export_query(
            conn, "sip_summary.csv",
            """SELECT sip_status, COUNT(*) AS registrations,
                      SUM(monthly_amount) AS registered_monthly_value_inr
               FROM sips GROUP BY sip_status ORDER BY sip_status""",
        )

    print(f"Exported {len(counts)} CSV files to: {EXPORT_DIR}")
    for filename, row_count in counts.items():
        print(f"  {filename}: {row_count:,} rows")
    print("All records are synthetic. Flows are not AUM, returns, or realized revenue.")


if __name__ == "__main__":
    main()
