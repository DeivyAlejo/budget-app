from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

INCOME_TYPES = ('salary', 'freelance', 'bonus', 'other')


class IncomeCreate(BaseModel):
    description: str = Field(min_length=1, max_length=500)
    amount: Decimal = Field(gt=0)
    income_type: str = Field(min_length=1, max_length=50)
    received_at: date


class IncomeUpdate(BaseModel):
    description: str = Field(min_length=1, max_length=500)
    amount: Decimal = Field(gt=0)
    income_type: str = Field(min_length=1, max_length=50)
    received_at: date


class IncomeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    description: str
    amount: Decimal
    income_type: str
    received_at: date
    created_at: datetime
