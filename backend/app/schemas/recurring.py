from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class RecurringTemplateCreate(BaseModel):
    category_id: int
    payment_method_id: int
    description: str = Field(min_length=1, max_length=500)
    amount: Decimal = Field(gt=0)
    day_of_month: int = Field(ge=1, le=31)
    frequency: str = Field(default="monthly")
    is_active: bool = Field(default=True)
    notes: str | None = Field(default=None, max_length=500)


class RecurringTemplateUpdate(BaseModel):
    category_id: int | None = None
    payment_method_id: int | None = None
    description: str | None = Field(default=None, min_length=1, max_length=500)
    amount: Decimal | None = Field(default=None, gt=0)
    day_of_month: int | None = Field(default=None, ge=1, le=31)
    frequency: str | None = None
    is_active: bool | None = None
    notes: str | None = Field(default=None, max_length=500)


class RecurringTemplateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category_id: int
    payment_method_id: int
    description: str
    amount: Decimal
    day_of_month: int
    frequency: str
    is_active: bool
    last_generated_year: int | None
    last_generated_month: int | None
    notes: str | None
    created_at: datetime
    updated_at: datetime


class GenerationSummary(BaseModel):
    template_id: int
    created_count: int
    total_amount: Decimal
    month: int
    year: int
