from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ExpenseCreate(BaseModel):
    category_id: int
    payment_method_id: int
    description: str = Field(min_length=1, max_length=500)
    amount: Decimal = Field(gt=0)
    spent_at: date


class ExpenseUpdate(BaseModel):
    category_id: int
    payment_method_id: int
    description: str = Field(min_length=1, max_length=500)
    amount: Decimal = Field(gt=0)
    spent_at: date


class ExpenseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category_id: int
    payment_method_id: int
    description: str
    amount: Decimal
    spent_at: date
    created_at: datetime
