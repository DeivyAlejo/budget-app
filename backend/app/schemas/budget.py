from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class BudgetCategoryAllocationWrite(BaseModel):
    category_id: int
    allocated_amount: Decimal = Field(gt=0)


class BudgetCategoryAllocationRead(BaseModel):
    category_id: int
    category_name: str
    allocated_amount: Decimal


class BudgetAllocationsUpdate(BaseModel):
    allocations: list[BudgetCategoryAllocationWrite]


class BudgetCreate(BaseModel):
    year: int = Field(ge=2000, le=2100)
    month: int = Field(ge=1, le=12)
    planned_amount: Decimal | None = Field(default=None, gt=0)
    copy_previous_month: bool = False


class BudgetUpdate(BaseModel):
    planned_amount: Decimal = Field(gt=0)


class BudgetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    year: int
    month: int
    planned_amount: Decimal
    copied_from_budget_id: int | None = None
    created_at: datetime
    updated_at: datetime
