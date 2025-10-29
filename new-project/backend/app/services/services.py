from typing import List, Optional, Tuple
from sqlalchemy.orm import Session

# Avoid importing from the `app.services` package during package init to
# prevent circular imports. Import the data access (dao) and models from
# their sibling packages.
from ..utils import dao
from ..models import Customer, Transaction
from ..models.models import KbDoc


class CustomerService:
    def __init__(self, db: Session):
        self.db = db

    def get_customer(self, customer_id: str) -> Optional[Customer]:
        return dao.get_customer(self.db, customer_id)

    def get_transactions(self, customer_id: str, limit: int = 50, cursor: Optional[str] = None) -> Tuple[List[Transaction], Optional[str]]:
        return dao.get_transactions_by_customer(self.db, customer_id, limit=limit, cursor_ts=cursor)

    def search_kb(self, q: str) -> List[KbDoc]:
        return dao.search_kb(self.db, q)
