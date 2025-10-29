"""Routes package initializer.

This module imports and exposes the domain route modules so callers
can do `from app.routes import case_routes` (as `app.main` expects).

Keep imports lightweight (modules only) to avoid running heavy side
effects at import time.
"""
from . import case_routes, customer_routes, knowledge_routes, transaction_routes

__all__ = [
    "case_routes",
    "customer_routes",
    "knowledge_routes",
    "transaction_routes",
]
