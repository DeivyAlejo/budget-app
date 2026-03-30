from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class CategoryTotal(BaseModel):
    category_id: int
    category_name: str
    total_amount: Decimal


class CategoryExpensesReport(BaseModel):
    category_id: int
    category_name: str
    total_amount: Decimal
    expenses: list[dict]


class ExpenseLine(BaseModel):
    expense_id: int
    description: str
    amount: Decimal
    spent_at: date
