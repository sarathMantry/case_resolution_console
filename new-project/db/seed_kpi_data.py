"""
Script to populate the database with sample alerts, cases, and triage runs.

Run this script to generate realistic test data for the dashboard KPIs.
Usage: python seed_kpi_data.py
"""
import sys
import os
import random
import uuid
from datetime import datetime, timedelta

# Add backend directory to path to allow imports
backend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backend')
sys.path.insert(0, backend_path)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Alert, Case, TriageRun, Customer, Transaction, Card

# Build DATABASE_URL from environment or defaults
DB_HOST = os.getenv('DB_HOST', os.getenv('POSTGRES_HOST', 'localhost'))
DB_PORT = os.getenv('DB_PORT', '5432')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'root')
DB_NAME = os.getenv('DB_NAME', 'postgres')

DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


def generate_sample_data(session, num_alerts=50, num_cases=30, num_triage_runs=40):
    """Generate and insert sample data into the database."""
    
    print("🔍 Checking for existing data...")
    
    # Check if we have customers and transactions
    customer_count = session.query(Customer).count()
    transaction_count = session.query(Transaction).count()
    
    print(f"Found {customer_count} customers and {transaction_count} transactions")
    
    # Get existing customers and transactions
    customers = session.query(Customer).limit(20).all()
    transactions = session.query(Transaction).limit(50).all()
    
    # If no customers exist, create some
    if not customers:
        print("📦 Creating sample customers...")
        for i in range(10):
            customer = Customer(
                id=str(uuid.uuid4()),
                name=f"Customer {i+1}",
                email_masked=f"cust{i+1}@*****.com",
                kyc_level="verified",
                created_at=datetime.utcnow() - timedelta(days=random.randint(30, 365))
            )
            session.add(customer)
        session.commit()
        customers = session.query(Customer).all()
        print(f"✅ Created {len(customers)} customers")
    
    # If no transactions exist, create some
    if not transactions:
        print("📦 Creating sample transactions...")
        for customer in customers[:5]:
            # Get or create a card for this customer
            card = session.query(Card).filter(Card.customer_id == customer.id).first()
            if not card:
                card = Card(
                    id=str(uuid.uuid4()),
                    customer_id=customer.id,
                    last4=str(random.randint(1000, 9999)),
                    network=random.choice(["VISA", "MASTERCARD", "AMEX"]),
                    status="ACTIVE",
                    created_at=datetime.utcnow() - timedelta(days=180)
                )
                session.add(card)
                session.flush()
            
            # Create transactions for this customer
            for _ in range(10):
                txn = Transaction(
                    id=str(uuid.uuid4()),
                    customer_id=customer.id,
                    card_id=card.id,
                    mcc=str(random.randint(1000, 9999)),
                    merchant=random.choice([
                        "Amazon", "Walmart", "Target", "Starbucks", "Shell Gas",
                        "McDonald's", "Netflix", "Spotify", "Uber", "DoorDash"
                    ]),
                    amount_cents=random.randint(500, 50000),
                    currency="USD",
                    ts=datetime.utcnow() - timedelta(days=random.randint(0, 90)),
                    device_id=f"device-{random.randint(1000, 9999)}",
                    country="US",
                    city=random.choice(["New York", "Los Angeles", "Chicago", "Houston", "Phoenix"])
                )
                session.add(txn)
        session.commit()
        transactions = session.query(Transaction).all()
        print(f"✅ Created {len(transactions)} transactions")
    
    # Generate Alerts
    print(f"\n📊 Generating {num_alerts} alerts...")
    # Align with DB constraints (003_alerts_and_cases.sql)
    alert_statuses = ["OPEN", "IN_REVIEW", "CLOSED"]
    risk_levels = ["LOW", "MEDIUM", "HIGH"]
    
    # Ensure every customer has at least one transaction and build a lookup
    txns_by_customer = {}
    for t in session.query(Transaction).all():
        txns_by_customer.setdefault(t.customer_id, []).append(t)

    customers_with_no_txns = [c for c in customers if len(txns_by_customer.get(c.id, [])) == 0]
    if customers_with_no_txns:
        print(f"📦 Backfilling transactions for {len(customers_with_no_txns)} customers with none...")
        for customer in customers_with_no_txns:
            # Get or create a card for this customer
            card = session.query(Card).filter(Card.customer_id == customer.id).first()
            if not card:
                card = Card(
                    id=str(uuid.uuid4()),
                    customer_id=customer.id,
                    last4=str(random.randint(1000, 9999)),
                    network=random.choice(["VISA", "MASTERCARD", "AMEX"]),
                    status="ACTIVE",
                    created_at=datetime.utcnow() - timedelta(days=180)
                )
                session.add(card)
                session.flush()

            # Create a few transactions for this customer
            for _ in range(random.randint(3, 8)):
                txn = Transaction(
                    id=str(uuid.uuid4()),
                    customer_id=customer.id,
                    card_id=card.id,
                    mcc=str(random.randint(1000, 9999)),
                    merchant=random.choice([
                        "Amazon", "Walmart", "Target", "Starbucks", "Shell Gas",
                        "McDonald's", "Netflix", "Spotify", "Uber", "DoorDash"
                    ]),
                    amount_cents=random.randint(500, 50000),
                    currency="USD",
                    ts=datetime.utcnow() - timedelta(days=random.randint(0, 90)),
                    device_id=f"device-{random.randint(1000, 9999)}",
                    country="US",
                    city=random.choice(["New York", "Los Angeles", "Chicago", "Houston", "Phoenix"])
                )
                session.add(txn)
                txns_by_customer.setdefault(customer.id, []).append(txn)
        session.commit()
        print("✅ Backfill complete.")

    # Refresh helper lists
    transactions = session.query(Transaction).all()
    customers_with_txns = [c for c in customers if len(txns_by_customer.get(c.id, [])) > 0]

    alerts_created = []
    for i in range(num_alerts):
        customer = random.choice(customers_with_txns)
        cust_txns = txns_by_customer.get(customer.id, [])
        transaction = random.choice(cust_txns)
        
        alert = Alert(
            id=str(uuid.uuid4()),
            customer_id=customer.id,
            suspect_txn_id=transaction.id,
            created_at=datetime.utcnow() - timedelta(hours=random.randint(0, 168)),
            risk=random.choice(risk_levels),
            status=random.choice(alert_statuses)
        )
        session.add(alert)
        alerts_created.append(alert)
    
    session.commit()
    print(f"✅ Created {len(alerts_created)} alerts")
    
    # Count alerts by status
    status_counts = {}
    for alert in alerts_created:
        status_counts[alert.status] = status_counts.get(alert.status, 0) + 1
    print(f"   Alert status breakdown: {status_counts}")
    
    # Generate Cases
    print(f"\n📋 Generating {num_cases} cases...")
    case_types = ["dispute", "fraud_investigation", "chargeback", "inquiry", "complaint"]
    case_statuses = ["open", "in_progress", "pending_review", "closed", "resolved"]
    reason_codes = ["10.4", "13.1", "4837", "4863", "unauthorized", "not_received", "defective"]
    
    cases_created = []
    for i in range(num_cases):
        customer = random.choice(customers)
        cust_txns = [t for t in transactions if t.customer_id == customer.id]
        transaction = random.choice(cust_txns) if cust_txns else None
        
        case = Case(
            id=str(uuid.uuid4()),
            customer_id=customer.id,
            txn_id=transaction.id if transaction else None,
            type=random.choice(case_types),
            status=random.choice(case_statuses),
            reason_code=random.choice(reason_codes),
            created_at=datetime.utcnow() - timedelta(days=random.randint(0, 60))
        )
        session.add(case)
        cases_created.append(case)
    
    session.commit()
    print(f"✅ Created {len(cases_created)} cases")
    
    # Count cases by type and status
    type_counts = {}
    status_counts = {}
    for case in cases_created:
        type_counts[case.type] = type_counts.get(case.type, 0) + 1
        status_counts[case.status] = status_counts.get(case.status, 0) + 1
    print(f"   Case type breakdown: {type_counts}")
    print(f"   Case status breakdown: {status_counts}")
    
    # Generate Triage Runs
    print(f"\n🔄 Generating {num_triage_runs} triage runs...")
    
    # Get alerts that can have triage runs
    available_alerts = [a for a in alerts_created if a.status in ["OPEN", "IN_REVIEW"]]
    
    triage_runs_created = []
    for i in range(min(num_triage_runs, len(available_alerts))):
        alert = random.choice(available_alerts)
        
        started = datetime.utcnow() - timedelta(hours=random.randint(0, 72))
        latency = random.randint(200, 2000)  # 200ms to 2000ms
        ended = started + timedelta(milliseconds=latency)
        
        triage_run = TriageRun(
            id=str(uuid.uuid4()),
            alert_id=alert.id,
            started_at=started,
            ended_at=ended,
            risk=random.choice(risk_levels),
            reasons={"reasons": [
                random.choice([
                    "Unusual transaction pattern",
                    "High velocity spending",
                    "Geographic anomaly",
                    "Device change detected",
                    "Merchant category mismatch"
                ]) for _ in range(random.randint(1, 3))
            ]},
            fallback_used=random.choice([True, False]),
            latency_ms=latency
        )
        session.add(triage_run)
        triage_runs_created.append(triage_run)
    
    session.commit()
    print(f"✅ Created {len(triage_runs_created)} triage runs")
    
    # Calculate average latency
    if triage_runs_created:
        avg_latency = sum(tr.latency_ms for tr in triage_runs_created) / len(triage_runs_created)
        print(f"   Average latency: {avg_latency:.0f}ms")
    
    print("\n✨ Sample data generation complete!")
    print("\n📈 KPI Summary:")
    print(f"   Alerts in queue: {sum(1 for a in alerts_created if a.status.lower() in ['open', 'in_review'])}")
    print(f"   Disputes opened: {sum(1 for c in cases_created if 'dispute' in c.type.lower() and c.status.lower() == 'open')}")
    print(f"   Triage runs: {len(triage_runs_created)}")


def main():
    """Main entry point for the script."""
    print("🚀 Starting KPI data seed script...\n")
    print(f"📍 Connecting to: {DATABASE_URL.replace(DB_PASSWORD, '****')}\n")
    
    # Create engine and session
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    try:
        generate_sample_data(
            session,
            num_alerts=50,
            num_cases=30,
            num_triage_runs=40
        )
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()
        raise
    finally:
        session.close()
    
    print("\n✅ Script completed successfully!")


if __name__ == "__main__":
    main()
