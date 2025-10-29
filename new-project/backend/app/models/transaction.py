"""Transaction and payment-related models."""
from sqlalchemy import Column, String, DateTime, BigInteger, ForeignKey, func, JSON
from sqlalchemy import TIMESTAMP
from sqlalchemy.orm import relationship
from .base import Base


class Transaction(Base):
    __tablename__ = "transactions"



class TransactionTrace(Base):
    __tablename__ = "transaction_traces"

"""Compatibility wrapper: transaction models live in `models.py`.

Re-export the canonical classes from `app.models.models`.
"""
from .models import Transaction, TransactionTrace

__all__ = ["Transaction", "TransactionTrace"]