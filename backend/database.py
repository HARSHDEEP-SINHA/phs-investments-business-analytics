"""SQLite schema and deterministic synthetic data for the portfolio application."""
from __future__ import annotations

import os
import random
import sqlite3
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "app.db"


def db_path() -> Path:
    configured = os.getenv("DATABASE_PATH", str(DEFAULT_DB))
    path = Path(configured)
    if not path.is_absolute():
        path = ROOT / path
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def create_schema(conn: sqlite3.Connection) -> None:
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS clients (
      client_id TEXT PRIMARY KEY,
      client_name TEXT NOT NULL,
      city TEXT NOT NULL,
      client_segment TEXT NOT NULL,
      acquisition_channel TEXT NOT NULL,
      join_date TEXT NOT NULL,
      client_status TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS schemes (
      scheme_id TEXT PRIMARY KEY,
      scheme_name TEXT NOT NULL,
      amc_name TEXT NOT NULL,
      category TEXT NOT NULL,
      risk_level TEXT NOT NULL,
      illustrative_commission_rate REAL NOT NULL
    );
    CREATE TABLE IF NOT EXISTS sips (
      sip_id TEXT PRIMARY KEY,
      client_id TEXT NOT NULL REFERENCES clients(client_id),
      scheme_id TEXT NOT NULL REFERENCES schemes(scheme_id),
      monthly_amount REAL NOT NULL,
      start_date TEXT NOT NULL,
      sip_status TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS transactions (
      transaction_id TEXT PRIMARY KEY,
      client_id TEXT NOT NULL REFERENCES clients(client_id),
      scheme_id TEXT NOT NULL REFERENCES schemes(scheme_id),
      sip_id TEXT REFERENCES sips(sip_id),
      transaction_date TEXT NOT NULL,
      transaction_type TEXT NOT NULL,
      amount_inr REAL NOT NULL CHECK(amount_inr >= 0),
      transaction_status TEXT NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(transaction_date);
    CREATE INDEX IF NOT EXISTS idx_transactions_client ON transactions(client_id);
    CREATE INDEX IF NOT EXISTS idx_transactions_scheme ON transactions(scheme_id);
    """)


def seed_if_empty(conn: sqlite3.Connection) -> None:
    if conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0] > 0:
        return

    rng = random.Random(20261010)
    start = date(2024, 1, 1)
    end = date(2025, 12, 31)
    days = (end - start).days
    def rand_date() -> str:
        return (start + timedelta(days=rng.randint(0, days))).isoformat()

    cities = ["Noida", "Delhi", "Gurugram", "Jaipur", "Mumbai", "Pune", "Bengaluru", "Hyderabad", "Kolkata", "Chennai", "Ranchi", "Lucknow"]
    segments = ["Mass Market", "Emerging Affluent", "Affluent", "High Net Worth"]
    channels = ["Referral", "Digital", "Branch", "Partner", "Campaign"]
    first_names = ["Aarav", "Vivaan", "Ananya", "Diya", "Rohan", "Priya", "Ishaan", "Kavya", "Rahul", "Meera", "Arjun", "Neha"]
    last_names = ["Sharma", "Verma", "Gupta", "Singh", "Kumar", "Patel", "Mehta", "Sinha", "Das", "Joshi"]
    clients = []
    for i in range(1, 1201):
        clients.append((f"CL{i:05d}", f"{rng.choice(first_names)} {rng.choice(last_names)}", rng.choice(cities),
                       rng.choices(segments, [45, 30, 20, 5])[0], rng.choice(channels), rand_date(),
                       rng.choices(["Active", "Inactive"], [88, 12])[0]))
    conn.executemany("INSERT INTO clients VALUES (?,?,?,?,?,?,?)", clients)

    categories = ["Equity", "Debt", "Hybrid", "Index", "Liquid"]
    schemes = []
    for i in range(1, 61):
        category = rng.choices(categories, [40, 20, 15, 15, 10])[0]
        risk = {"Equity":"High", "Debt":"Low to Moderate", "Hybrid":"Moderate to High", "Index":"Moderate to High", "Liquid":"Low"}[category]
        schemes.append((f"SCH{i:03d}", f"{category} Fund {i:02d}", f"Sample AMC {(i % 12) + 1:02d}",
                        category, risk, round(rng.uniform(0.002, 0.012), 5)))
    conn.executemany("INSERT INTO schemes VALUES (?,?,?,?,?,?)", schemes)

    client_ids = [x[0] for x in clients]
    scheme_ids = [x[0] for x in schemes]
    sips = []
    for i in range(1, 1801):
        sips.append((f"SIP{i:05d}", rng.choice(client_ids), rng.choice(scheme_ids),
                     float(rng.choice([500, 1000, 1500, 2000, 3000, 5000, 7500, 10000])),
                     rand_date(), rng.choices(["Active", "Paused", "Cancelled"], [72, 8, 20])[0]))
    conn.executemany("INSERT INTO sips VALUES (?,?,?,?,?,?)", sips)

    sip_ids = [x[0] for x in sips]
    transactions = []
    types = ["PURCHASE", "SIP_INSTALLMENT", "REDEMPTION", "SWITCH_IN", "SWITCH_OUT"]
    weights = [38, 34, 18, 5, 5]
    for i in range(1, 12001):
        txn_type = rng.choices(types, weights)[0]
        amount = float(rng.choice([500, 1000, 2000, 3000, 5000, 10000, 15000, 25000, 50000]))
        # Slight growth trend makes month-on-month analysis meaningful without hardcoding conclusions.
        txn_date = date.fromisoformat(rand_date())
        growth = 1 + max(0, txn_date.year - 2024) * 0.12
        amount = round(amount * growth, 2)
        sip_id = rng.choice(sip_ids) if txn_type == "SIP_INSTALLMENT" else None
        transactions.append((f"TXN{i:07d}", rng.choice(client_ids), rng.choice(scheme_ids), sip_id,
                             txn_date.isoformat(), txn_type, amount,
                             rng.choices(["Successful", "Failed"], [97, 3])[0]))
    conn.executemany("INSERT INTO transactions VALUES (?,?,?,?,?,?,?,?)", transactions)
    conn.commit()


def initialize_database() -> None:
    with connect() as conn:
        create_schema(conn)
        seed_if_empty(conn)
