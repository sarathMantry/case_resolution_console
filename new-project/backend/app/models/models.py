from sqlalchemy import Column, String, Integer, BigInteger, TIMESTAMP, Text, Boolean, JSON, ForeignKey, CHAR, func
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()



class Card(Base):
    __tablename__ = 'cards'
    id = Column(String(36), primary_key=True)
    customer_id = Column(String(36), ForeignKey('customers.id'), nullable=False)
    last4 = Column(CHAR(4), nullable=False)
    network = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False)
    created_at = Column(TIMESTAMP, nullable=False)

    customer = relationship('Customer', back_populates='cards')
    transactions = relationship('Transaction', back_populates='card')

class Account(Base):
    __tablename__ = 'accounts'
    id = Column(String(36), primary_key=True)
    customer_id = Column(String(36), ForeignKey('customers.id'), nullable=False)
    balance_cents = Column(BigInteger, nullable=False)
    currency = Column(CHAR(3), nullable=False)

    customer = relationship('Customer', back_populates='accounts')

class Customer(Base):
    __tablename__ = "customers"

    id = Column(String(36), primary_key=True)  # UUID v4
    name = Column(String(255), nullable=False)
    email_masked = Column(String(255), nullable=False)
    kyc_level = Column(String(20), nullable=False)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())

    # Relationships
    cards = relationship('Card', back_populates='customer')
    accounts = relationship('Account', back_populates='customer')
    alerts = relationship('Alert', back_populates='customer')
    cases = relationship('Case', back_populates='customer')
    transactions = relationship('Transaction', back_populates='customer')




class TriageRun(Base):
    __tablename__ = 'triage_runs'
    id = Column(String(36), primary_key=True)
    alert_id = Column(String(36), ForeignKey('alerts.id'), nullable=False)
    started_at = Column(TIMESTAMP, nullable=False)
    ended_at = Column(TIMESTAMP)
    risk = Column(Text, nullable=False)
    reasons = Column(JSON, nullable=False)
    fallback_used = Column(Boolean, nullable=False)
    latency_ms = Column(Integer)
    alert = relationship('Alert', back_populates='triage_runs')

class AgentTrace(Base):
    __tablename__ = 'agent_traces'
    run_id = Column(String(36), ForeignKey('triage_runs.id'), primary_key=True)
    seq = Column(Integer, primary_key=True)
    step = Column(Text, nullable=False)
    ok = Column(Boolean, nullable=False)
    duration_ms = Column(Integer, nullable=False)
    detail_json = Column(JSON)

class KbDoc(Base):
    __tablename__ = 'kb_docs'
    id = Column(String(36), primary_key=True)
    title = Column(String(255), nullable=False)
    anchor = Column(String(100), nullable=False)
    content_text = Column(Text, nullable=False)

class Policy(Base):
    __tablename__ = 'policies'
    id = Column(String(36), primary_key=True)
    code = Column(String(100), nullable=False)
    title = Column(String(255), nullable=False)
    content_text = Column(Text, nullable=False)


# Case & Alert models (moved here so all models live in a single module)
class Alert(Base):
    __tablename__ = "alerts"

    id = Column(String(36), primary_key=True)
    customer_id = Column(String(36), ForeignKey('customers.id', ondelete='CASCADE'))
    suspect_txn_id = Column(String(36), ForeignKey('transactions.id', ondelete='CASCADE'))
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    risk = Column(String, nullable=False)
    status = Column(String, nullable=False)

    customer = relationship('Customer', back_populates='alerts')
    transaction = relationship('Transaction', back_populates='alerts')
    triage_runs = relationship('TriageRun', back_populates='alert')


class Case(Base):
    __tablename__ = "cases"

    id = Column(String(36), primary_key=True)
    customer_id = Column(String(36), ForeignKey('customers.id', ondelete='CASCADE'))
    txn_id = Column(String(36), ForeignKey('transactions.id', ondelete='CASCADE'))
    type = Column(String, nullable=False)
    status = Column(String, nullable=False)
    reason_code = Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    customer = relationship('Customer', back_populates='cases')
    transaction = relationship('Transaction', back_populates='cases')
    events = relationship('CaseEvent', back_populates='case')


class CaseEvent(Base):
    __tablename__ = "case_events"

    id = Column(String(36), primary_key=True)
    case_id = Column(String(36), ForeignKey('cases.id', ondelete='CASCADE'))
    ts = Column(TIMESTAMP(timezone=True), server_default=func.now())
    actor = Column(String(255), nullable=False)
    action = Column(String, nullable=False)
    payload_json = Column(JSON)

    case = relationship('Case', back_populates='events')


# Transaction models
class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String(36), primary_key=True)
    customer_id = Column(String(36), ForeignKey('customers.id', ondelete='CASCADE'))
    card_id = Column(String(36), ForeignKey('cards.id', ondelete='CASCADE'))
    mcc = Column(String(4), nullable=False)
    merchant = Column(String(255), nullable=False)
    amount_cents = Column(BigInteger, nullable=False)
    currency = Column(String(3), nullable=False)
    ts = Column(TIMESTAMP(timezone=True), nullable=False)
    device_id = Column(String(64))
    country = Column(String(2), nullable=False)
    city = Column(String(100))

    customer = relationship('Customer', back_populates='transactions')
    card = relationship('Card', back_populates='transactions')
    alerts = relationship('Alert', back_populates='transaction')
    cases = relationship('Case', back_populates='transaction')
    traces = relationship('TransactionTrace', back_populates='transaction')


class TransactionTrace(Base):
    __tablename__ = "transaction_traces"

    id = Column(String(36), primary_key=True)
    txn_id = Column(String(36), ForeignKey('transactions.id', ondelete='CASCADE'))
    trace_json = Column(JSON, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    transaction = relationship('Transaction', back_populates='traces')
