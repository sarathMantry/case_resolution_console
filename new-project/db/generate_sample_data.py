#!/usr/bin/env python3
"""
Idempotent sample data generator for the case-resolution console database.

Features:
- Supports large batch inserts using execute_values for speed.
- Optional `--clean` flag to TRUNCATE all tables before inserting (idempotent run).
- `--yes` to skip confirmation when using --clean and truncating many rows.

This script expects a Postgres DSN in the form: postgresql://user:pass@host:port/dbname
"""
from __future__ import annotations

import json
import os
import random
import uuid
from datetime import datetime, timedelta
from typing import Dict

import click
import psycopg2
from psycopg2.extras import Json, execute_values
from dotenv import load_dotenv
from faker import Faker
from tqdm import tqdm


# Load environment variables from .env if present
load_dotenv()

fake = Faker()


class DataGenerator:
    TABLES_TO_TRUNCATE = [
        'case_events', 'cases', 'alerts',
        'agent_traces', 'triage_runs',
        'transactions', 'cards', 'accounts', 'customers',
        'kb_docs', 'policies'
    ]

    def __init__(self, dsn: str):
        self.dsn = dsn
        self.conn = psycopg2.connect(dsn)

    def close(self) -> None:
        try:
            self.conn.close()
        except Exception:
            pass

    def truncate_all(self) -> None:
        """Truncate all known tables using CASCADE. This makes seeding idempotent.

        WARNING: destructive. Caller should confirm before running.
        """
        with self.conn.cursor() as cur:
            sql = f"TRUNCATE TABLE {', '.join(self.TABLES_TO_TRUNCATE)} RESTART IDENTITY CASCADE;"
            cur.execute(sql)
        self.conn.commit()

    def generate_customers(self, count: int, batch: int = 1000) -> None:
        rows = []
        for _ in range(count):
            cid = str(uuid.uuid4())
            row = (cid, fake.name(), f"****@{fake.free_email_domain()}", random.choice(['BASIC', 'FULL', 'ENHANCED']), fake.date_time_between(start_date='-2y'))
            rows.append(row)

        with self.conn.cursor() as cur:
            for i in range(0, len(rows), batch):
                execute_values(cur, "INSERT INTO customers (id, name, email_masked, kyc_level, created_at) VALUES %s", rows[i:i+batch])
        self.conn.commit()

    def fetch_customer_ids(self) -> list[str]:
        with self.conn.cursor() as cur:
            cur.execute("SELECT id FROM customers ORDER BY created_at ASC")
            return [r[0] for r in cur.fetchall()]

    def generate_accounts_and_cards(self, customer_ids: list[str], avg_cards_per_customer: float = 1.0, batch: int = 1000) -> None:
        accounts = []
        cards = []
        for cid in customer_ids:
            aid = str(uuid.uuid4())
            accounts.append((aid, cid, random.randint(-1000000, 1000000), random.choice(['USD', 'EUR', 'GBP', 'INR'])))
            num_cards = max(1, int(round(random.gauss(avg_cards_per_customer, 0.5))))
            for _ in range(num_cards):
                cards.append((str(uuid.uuid4()), cid, fake.numerify('####'), random.choice(['VISA', 'MASTERCARD', 'AMEX']), random.choice(['ACTIVE', 'FROZEN', 'CLOSED']), fake.date_time_between(start_date='-5y')))

        with self.conn.cursor() as cur:
            for i in range(0, len(accounts), batch):
                execute_values(cur, "INSERT INTO accounts (id, customer_id, balance_cents, currency) VALUES %s", accounts[i:i+batch])
            for i in range(0, len(cards), batch):
                execute_values(cur, "INSERT INTO cards (id, customer_id, last4, network, status, created_at) VALUES %s", cards[i:i+batch])
        self.conn.commit()

    def generate_transactions(self, customer_ids: list[str], tx_per_customer: int = 100, batch: int = 5000) -> None:
        rows = []
        now = datetime.utcnow()
        for cid in tqdm(customer_ids, desc="customers"):
            for _ in range(tx_per_customer):
                tid = str(uuid.uuid4())
                amount_cents = random.randint(100, 1000000)
                ts = now - timedelta(seconds=random.randint(0, 60 * 60 * 24 * 365))
                merchant = fake.company()
                mcc = random.choice(['4111', '5411', '5812', '5999', '7011'])
                rows.append((tid, cid, cid, mcc, merchant, amount_cents, random.choice(['USD', 'EUR']), ts, fake.uuid4(), fake.country_code(), fake.city()))

                if len(rows) >= batch:
                    with self.conn.cursor() as cur:
                        execute_values(cur, "INSERT INTO transactions (id, customer_id, card_id, mcc, merchant, amount_cents, currency, ts, device_id, country, city) VALUES %s", rows)
                    self.conn.commit()
                    rows.clear()

        if rows:
            with self.conn.cursor() as cur:
                execute_values(cur, "INSERT INTO transactions (id, customer_id, card_id, mcc, merchant, amount_cents, currency, ts, device_id, country, city) VALUES %s", rows)
            self.conn.commit()

    def generate_alerts_and_cases(self) -> None:
        # Lightweight alerts and cases generation to seed the system
        with self.conn.cursor() as cur:
            cur.execute("SELECT id, card_id, ts FROM transactions ORDER BY ts DESC LIMIT 1000")
            recent = cur.fetchall()

        alerts = []
        cases = []
        events = []
        for r in recent:
            if random.random() < 0.05:
                alert_id = str(uuid.uuid4())
                alerts.append((alert_id, r[0], r[0], r[2], random.choice(['LOW', 'MEDIUM', 'HIGH']), random.choice(['OPEN', 'IN_REVIEW', 'CLOSED'])))
                if random.random() < 0.3:
                    case_id = str(uuid.uuid4())
                    cases.append((case_id, r[0], r[0], random.choice(['FRAUD', 'DISPUTE']), random.choice(['OPEN', 'IN_PROGRESS', 'RESOLVED']), f"REASON_{random.randint(1,100)}", r[2]))
                    events.append((str(uuid.uuid4()), case_id, r[2], f"agent_{random.randint(1,10)}", random.choice(['REVIEW','FREEZE_CARD','CONTACT_CUSTOMER']), Json({'note': fake.text(max_nb_chars=60)})))

        if alerts:
            with self.conn.cursor() as cur:
                execute_values(cur, "INSERT INTO alerts (id, customer_id, suspect_txn_id, created_at, risk, status) VALUES %s", alerts)
                if cases:
                    execute_values(cur, "INSERT INTO cases (id, customer_id, txn_id, type, status, reason_code, created_at) VALUES %s", cases)
                    execute_values(cur, "INSERT INTO case_events (id, case_id, ts, actor, action, payload_json) VALUES %s", events)
            self.conn.commit()

    def generate_kb_and_policies(self) -> None:
        kb_docs = []
        policies = []
        for i in range(10):
            kb_docs.append((str(uuid.uuid4()), f"KB Article {i+1}", f"kb-{i+1}", fake.text(max_nb_chars=800)))
        for i in range(5):
            policies.append((str(uuid.uuid4()), f"POL_{i+1}", f"Policy {i+1}", fake.text(max_nb_chars=400)))

        with self.conn.cursor() as cur:
            execute_values(cur, "INSERT INTO kb_docs (id, title, anchor, content_text) VALUES %s", kb_docs)
            execute_values(cur, "INSERT INTO policies (id, code, title, content_text) VALUES %s", policies)
        self.conn.commit()


@click.command()
@click.option('--db', 'db_dsn', default=lambda: os.environ.get('DATABASE_URL', ''), help='Postgres DSN, e.g. postgresql://user:pw@host:5432/db')
@click.option('--customers', default=1000, help='Number of customers to create')
@click.option('--tx-per-customer', default=100, help='Transactions per customer')
@click.option('--avg-cards-per-customer', default=1.0, help='Average cards per customer')
@click.option('--clean', is_flag=True, help='TRUNCATE target tables before inserting (destructive)')
@click.option('--yes', is_flag=True, help='Skip confirmation prompts')
def main(db_dsn: str, customers: int, tx_per_customer: int, avg_cards_per_customer: float, clean: bool, yes: bool) -> None:
    if not db_dsn:
        raise click.UsageError('Database DSN required via --db or DATABASE_URL env var')

    gen = DataGenerator(db_dsn)
    try:
        if clean:
            if not yes:
                click.confirm(f"This will TRUNCATE tables: {', '.join(DataGenerator.TABLES_TO_TRUNCATE)}. Continue?", abort=True)
            click.echo('Truncating tables...')
            gen.truncate_all()

        click.echo(f'Generating {customers} customers...')
        gen.generate_customers(customers)
        customer_ids = gen.fetch_customer_ids()[-customers:]

        click.echo('Generating accounts and cards...')
        gen.generate_accounts_and_cards(customer_ids, avg_cards_per_customer)

        click.echo('Generating transactions...')
        gen.generate_transactions(customer_ids, tx_per_customer)

        click.echo('Generating alerts, cases, and KB/policies...')
        gen.generate_alerts_and_cases()
        gen.generate_kb_and_policies()

        click.echo('\nDone.')
    finally:
        gen.close()


if __name__ == '__main__':
    main()
