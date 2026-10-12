"""Export the local synthetic SQLite model for BI tools such as Power BI.

Run from the repository root:
    python -m scripts.export_powerbi_data

All exported records are synthetic. Files are generated locally and should not be committed.
"""
from __future__ import annotations

import csv
import json
import sqlite3
from pathlib import Path

from backend.database import connect, initialize_database

ROOT = Path(__file__).resolve().parents[1]
EXPORT_DIR = ROOT / "exports"

TABLES = ("clients", "schemes", "sips", "transactions")


def export_query(conn: sqlite3.Connection, filename: str, query: str) -> int:
    cursor = conn.execute(query)
    rows = cursor.fetchall()
    columns = [description[0] for description in cursor.description]
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    with (EXPORT_DIR / filename).open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.writer(handle)
        writer.writerow(columns)
        writer.writerows(rows)
    return len(rows)


def build_quality_report(conn: sqlite3.Connection) -> dict:
    counts = {
        table: conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        for table in TABLES
    }
    fk_violations = conn.execute("PRAGMA foreign_key_check").fetchall()
    null_transaction_ids = conn.execute(
        "SELECT COUNT(*) FROM transactions WHERE transaction_id IS NULL OR TRIM(transaction_id) = ''"
    ).fetchone()[0]
    negative_amounts = conn.execute(
        "SELECT COUNT(*) FROM transactions WHERE amount_inr < 0"
    ).fetchone()[0]
    duplicate_transaction_ids = conn.execute("""
        SELECT COUNT(*) FROM (
            SELECT transaction_id FROM transactions
            GROUP BY transaction_id HAVING COUNT(*) > 1
        )
    """).fetchone()[0]
    status_counts = {
        row[0]: row[1]
        for row in conn.execute(
            "SELECT transaction_status, COUNT(*) FROM transactions GROUP BY transaction_status"
        ).fetchall()
    }
    return {
        "synthetic_data": True,
        "row_counts": counts,
        "quality_checks": {
            "foreign_key_violations": len(fk_violations),
            "blank_transaction_ids": null_transaction_ids,
            "negative_transaction_amounts": negative_amounts,
            "duplicate_transaction_id_groups": duplicate_transaction_ids,
        },
        "transaction_status_counts": status_counts,
    }


def main() -> None:
    initialize_database()
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    with connect() as conn:
        exported = {}
        for table in TABLES:
            exported[f"{table}.csv"] = export_query(
                conn, f"{table}.csv", f"SELECT * FROM {table} ORDER BY 1"
            )

        # Curated fact tables keep report-building simple and consistent with the app's KPI definitions.
        curated_queries = {
            "monthly_trend.csv": """
                SELECT substr(transaction_date, 1, 7) AS month,
                       SUM(CASE WHEN transaction_status='Successful'
                                  AND transaction_type IN ('PURCHASE','SIP_INSTALLMENT','SWITCH_IN')
                                THEN amount_inr ELSE 0 END) AS inflows_inr,
                       SUM(CASE WHEN transaction_status='Successful'
                                  AND transaction_type IN ('REDEMPTION','SWITCH_OUT')
                                THEN amount_inr ELSE 0 END) AS outflows_inr,
                       SUM(CASE WHEN transaction_status='Successful'
                                  AND transaction_type IN ('PURCHASE','SIP_INSTALLMENT','SWITCH_IN')
                                THEN amount_inr
                                WHEN transaction_status='Successful'
                                  AND transaction_type IN ('REDEMPTION','SWITCH_OUT')
                                THEN -amount_inr ELSE 0 END) AS net_flows_inr,
                       SUM(CASE WHEN transaction_status='Successful' THEN 1 ELSE 0 END) AS successful_transactions,
                       SUM(CASE WHEN transaction_status='Failed' THEN 1 ELSE 0 END) AS failed_transactions
                FROM transactions
                GROUP BY substr(transaction_date, 1, 7)
                ORDER BY month
            """,
            "city_performance.csv": """
                SELECT c.city,
                       SUM(CASE WHEN t.transaction_status='Successful'
                                  AND t.transaction_type IN ('PURCHASE','SIP_INSTALLMENT','SWITCH_IN')
                                THEN t.amount_inr ELSE 0 END) AS inflows_inr,
                       SUM(CASE WHEN t.transaction_status='Successful'
                                  AND t.transaction_type IN ('REDEMPTION','SWITCH_OUT')
                                THEN t.amount_inr ELSE 0 END) AS outflows_inr,
                       SUM(CASE WHEN t.transaction_status='Successful'
                                  AND t.transaction_type IN ('PURCHASE','SIP_INSTALLMENT','SWITCH_IN')
                                THEN t.amount_inr
                                WHEN t.transaction_status='Successful'
                                  AND t.transaction_type IN ('REDEMPTION','SWITCH_OUT')
                                THEN -t.amount_inr ELSE 0 END) AS net_flows_inr,
                       COUNT(DISTINCT CASE WHEN t.transaction_status='Successful' THEN t.client_id END) AS transacting_clients
                FROM transactions t JOIN clients c ON c.client_id=t.client_id
                GROUP BY c.city
                ORDER BY inflows_inr DESC
            """,
            "scheme_performance.csv": """
                SELECT s.scheme_id, s.scheme_name, s.category,
                       SUM(CASE WHEN t.transaction_status='Successful'
                                  AND t.transaction_type IN ('PURCHASE','SIP_INSTALLMENT','SWITCH_IN')
                                THEN t.amount_inr ELSE 0 END) AS inflows_inr,
                       SUM(CASE WHEN t.transaction_status='Successful'
                                  AND t.transaction_type IN ('REDEMPTION','SWITCH_OUT')
                                THEN t.amount_inr ELSE 0 END) AS outflows_inr,
                       SUM(CASE WHEN t.transaction_status='Successful'
                                  AND t.transaction_type IN ('PURCHASE','SIP_INSTALLMENT','SWITCH_IN')
                                THEN t.amount_inr
                                WHEN t.transaction_status='Successful'
                                  AND t.transaction_type IN ('REDEMPTION','SWITCH_OUT')
                                THEN -t.amount_inr ELSE 0 END) AS net_flows_inr,
                       COUNT(CASE WHEN t.transaction_status='Successful' THEN 1 END) AS successful_transactions
                FROM schemes s LEFT JOIN transactions t ON t.scheme_id=s.scheme_id
                GROUP BY s.scheme_id, s.scheme_name, s.category
                ORDER BY inflows_inr DESC
            """,
            "sip_status_summary.csv": """
                SELECT sip_status, COUNT(*) AS registrations,
                       SUM(monthly_amount) AS registered_monthly_value_inr
                FROM sips
                GROUP BY sip_status
                ORDER BY sip_status
            """,

            "transaction_failure_by_type.csv": """
                SELECT
                    transaction_type,
                    COUNT(*) AS total_transactions,
                    SUM(CASE WHEN transaction_status = 'Failed'
                             THEN 1 ELSE 0 END) AS failed_transactions,
                    ROUND(
                        100.0 * SUM(CASE WHEN transaction_status = 'Failed'
                                         THEN 1 ELSE 0 END) / COUNT(*),
                        2
                    ) AS failure_pct
                FROM transactions
                GROUP BY transaction_type
                ORDER BY failure_pct DESC
            """,
            "monthly_failure_trend.csv": """
                SELECT
                    substr(transaction_date, 1, 7) AS month,
                    COUNT(*) AS total_transactions,
                    SUM(CASE WHEN transaction_status = 'Failed'
                             THEN 1 ELSE 0 END) AS failed_transactions,
                    SUM(CASE WHEN transaction_status = 'Successful'
                             THEN 1 ELSE 0 END) AS successful_transactions,
                    ROUND(
                        100.0 * SUM(CASE WHEN transaction_status = 'Failed'
                                         THEN 1 ELSE 0 END) / COUNT(*),
                        2
                    ) AS failure_pct
                FROM transactions
                GROUP BY substr(transaction_date, 1, 7)
                ORDER BY month
            """,

        }
        for filename, query in curated_queries.items():
            exported[filename] = export_query(conn, filename, query)

        report = build_quality_report(conn)
        (EXPORT_DIR / "data_quality_report.json").write_text(
            json.dumps(report, indent=2), encoding="utf-8"
        )

    print(f"Exported synthetic BI data to: {EXPORT_DIR}")
    for filename, count in exported.items():
        print(f"  {filename}: {count:,} rows")
    print("  data_quality_report.json: written")
    print("Quality checks:")
    for name, value in report["quality_checks"].items():
        print(f"  {name}: {value}")


if __name__ == "__main__":
    main()
