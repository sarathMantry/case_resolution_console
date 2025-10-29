"""Compatibility wrapper: all case models live in `models.py`.

This file re-exports the classes from `app.models.models` so existing
imports like `from ..models.case import Case` continue to work while the
single canonical source of model definitions remains `models.py`.
"""
from .models import Alert, Case, CaseEvent

__all__ = ["Alert", "Case", "CaseEvent"]