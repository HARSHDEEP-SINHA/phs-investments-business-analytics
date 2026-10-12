"""Fixed, read-only analytics queries. User text is never interpolated into SQL."""
from __future__ import annotations

from .database import connect


def overview() -> dict:
    with connect() as conn:
        totals = conn.execute("""
          SELECT
            SUM(CASE WHEN transaction_status='Successful' AND transaction_type IN ('PURCHASE','SIP_INSTALLMENT','SWITCH_IN') THEN amount_inr ELSE 0 END) AS inflows,
            SUM(CASE WHEN transaction_status='Successful' AND transaction_type IN ('REDEMPTION','SWITCH_OUT') THEN amount_inr ELSE 0 END) AS outflows,
            COUNT(DISTINCT CASE WHEN transaction_status='Successful' THEN client_id END) AS transacting_clients,
            SUM(CASE WHEN transaction_status='Successful' THEN 1 ELSE 0 END) AS successful_transactions,
            SUM(CASE WHEN transaction_status='Failed' THEN 1 ELSE 0 END) AS failed_transactions
          FROM transactions
        """).fetchone()
        active_clients = conn.execute("SELECT COUNT(*) FROM clients WHERE client_status='Active'").fetchone()[0]
        active_sips = conn.execute("SELECT COUNT(*) FROM sips WHERE sip_status='Active'").fetchone()[0]
        monthly_sip = conn.execute("SELECT SUM(monthly_amount) FROM sips WHERE sip_status='Active'").fetchone()[0] or 0
        total = dict(totals)
        inflows = total["inflows"] or 0
        outflows = total["outflows"] or 0
        return {
          "inflows_inr": round(inflows, 2), "outflows_inr": round(outflows, 2),
          "net_flows_inr": round(inflows - outflows, 2),
          "active_clients": active_clients, "transacting_clients": total["transacting_clients"] or 0,
          "active_sips": active_sips, "active_sip_monthly_value_inr": round(monthly_sip, 2),
          "successful_transactions": total["successful_transactions"] or 0,
          "failed_transactions": total["failed_transactions"] or 0,
          "synthetic_data": True
        }


def monthly_trend() -> list[dict]:
    with connect() as conn:
        rows = conn.execute("""
          SELECT substr(transaction_date,1,7) AS month,
            SUM(CASE WHEN transaction_type IN ('PURCHASE','SIP_INSTALLMENT','SWITCH_IN') THEN amount_inr ELSE 0 END) AS inflows,
            SUM(CASE WHEN transaction_type IN ('REDEMPTION','SWITCH_OUT') THEN amount_inr ELSE 0 END) AS outflows,
            COUNT(*) AS transaction_count
          FROM transactions WHERE transaction_status='Successful'
          GROUP BY substr(transaction_date,1,7) ORDER BY month
        """).fetchall()
    return [{"month": r["month"], "inflows_inr": round(r["inflows"] or 0, 2),
             "outflows_inr": round(r["outflows"] or 0, 2),
             "net_flows_inr": round((r["inflows"] or 0) - (r["outflows"] or 0), 2),
             "transaction_count": r["transaction_count"]} for r in rows]


def city_performance(limit: int = 10) -> list[dict]:
    limit = max(1, min(int(limit), 20))
    with connect() as conn:
        rows = conn.execute("""
          SELECT c.city,
            SUM(CASE WHEN t.transaction_type IN ('PURCHASE','SIP_INSTALLMENT','SWITCH_IN') THEN t.amount_inr ELSE 0 END) AS inflows,
            SUM(CASE WHEN t.transaction_type IN ('REDEMPTION','SWITCH_OUT') THEN t.amount_inr ELSE 0 END) AS outflows,
            COUNT(DISTINCT t.client_id) AS clients
          FROM transactions t JOIN clients c ON c.client_id=t.client_id
          WHERE t.transaction_status='Successful'
          GROUP BY c.city ORDER BY inflows DESC LIMIT ?
        """, (limit,)).fetchall()
    return [{"city": r["city"], "inflows_inr": round(r["inflows"] or 0, 2),
             "outflows_inr": round(r["outflows"] or 0, 2),
             "net_flows_inr": round((r["inflows"] or 0) - (r["outflows"] or 0), 2),
             "transacting_clients": r["clients"]} for r in rows]


def scheme_performance(limit: int = 10) -> list[dict]:
    limit = max(1, min(int(limit), 100))
    with connect() as conn:
        rows = conn.execute("""
          SELECT s.scheme_name, s.category,
            SUM(CASE WHEN t.transaction_type IN ('PURCHASE','SIP_INSTALLMENT','SWITCH_IN') THEN t.amount_inr ELSE 0 END) AS inflows,
            SUM(CASE WHEN t.transaction_type IN ('REDEMPTION','SWITCH_OUT') THEN t.amount_inr ELSE 0 END) AS outflows,
            COUNT(*) AS transactions
          FROM transactions t JOIN schemes s ON s.scheme_id=t.scheme_id
          WHERE t.transaction_status='Successful'
          GROUP BY s.scheme_id, s.scheme_name, s.category
          ORDER BY inflows DESC LIMIT ?
        """, (limit,)).fetchall()
    return [{"scheme_name": r["scheme_name"], "category": r["category"],
             "inflows_inr": round(r["inflows"] or 0, 2), "outflows_inr": round(r["outflows"] or 0, 2),
             "net_flows_inr": round((r["inflows"] or 0) - (r["outflows"] or 0), 2),
             "transactions": r["transactions"]} for r in rows]


def sip_summary() -> dict:
    with connect() as conn:
        rows = conn.execute("""
          SELECT sip_status, COUNT(*) AS sip_count, SUM(monthly_amount) AS monthly_value
          FROM sips GROUP BY sip_status ORDER BY sip_status
        """).fetchall()
    return {"statuses": [{"status": r["sip_status"], "count": r["sip_count"],
                          "monthly_value_inr": round(r["monthly_value"] or 0, 2)} for r in rows]}



def transaction_failures() -> dict:
    """Return aggregate failure counts and rates; never expose transaction-level records."""
    with connect() as conn:
        total = conn.execute("""
          SELECT COUNT(*) AS total,
            SUM(CASE WHEN transaction_status='Failed' THEN 1 ELSE 0 END) AS failed
          FROM transactions
        """).fetchone()
        by_type = conn.execute("""
          SELECT transaction_type, COUNT(*) AS total,
            SUM(CASE WHEN transaction_status='Failed' THEN 1 ELSE 0 END) AS failed
          FROM transactions GROUP BY transaction_type ORDER BY transaction_type
        """).fetchall()
        monthly = conn.execute("""
          SELECT substr(transaction_date,1,7) AS month, COUNT(*) AS total,
            SUM(CASE WHEN transaction_status='Failed' THEN 1 ELSE 0 END) AS failed
          FROM transactions GROUP BY substr(transaction_date,1,7) ORDER BY month
        """).fetchall()

    def row_summary(row, name_key=None):
        total_count = int(row["total"] or 0)
        failed_count = int(row["failed"] or 0)
        result = {"total_transactions": total_count, "failed_transactions": failed_count,
                  "failure_rate_pct": round(failed_count / total_count * 100, 2) if total_count else 0.0}
        if name_key:
            result[name_key] = row[name_key]
        return result

    return {
        **row_summary(total),
        "by_type": [
            {"transaction_type": row["transaction_type"], **row_summary(row)}
            for row in by_type
        ],
        "monthly": [
            {"month": row["month"], **row_summary(row)}
            for row in monthly
        ],
        "synthetic_data": True,
    }


def run_tool(tool_name: str) -> dict:
    """Allow-list for the AI layer: no arbitrary SQL and no writes."""
    tools = {
      "overview": overview,
      "monthly_trend": lambda: {"months": monthly_trend()},
      "city_performance": lambda: {"cities": city_performance(limit=20)},
      "city_comparison": lambda: {"cities": city_performance(limit=20)},
      "transaction_failures": transaction_failures,
      "scheme_performance": lambda: {"schemes": scheme_performance(limit=100)},
      "sip_summary": sip_summary,
    }
    if tool_name not in tools:
        raise ValueError("Unsupported analytics tool")
    return tools[tool_name]()
