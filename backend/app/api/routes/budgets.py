from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.budget import Budget
from app.models.budget_category_allocation import BudgetCategoryAllocation
from app.models.category import Category
from app.models.user import User
from app.models.user_hidden_category import UserHiddenCategory
from app.schemas.budget import (
    BudgetAllocationsUpdate,
    BudgetCategoryAllocationRead,
    BudgetCreate,
    BudgetRead,
    BudgetUpdate,
)

router = APIRouter(prefix="/budgets", tags=["budgets"])


def _previous_year_month(year: int, month: int) -> tuple[int, int]:
    if month == 1:
        return (year - 1, 12)
    return (year, month - 1)


def _get_budget_or_404(db: Session, budget_id: int, user_id: int) -> Budget:
    budget = db.get(Budget, budget_id)
    if not budget or budget.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found")
    return budget


@router.get("", response_model=list[BudgetRead])
def list_budgets(
    year: int | None = Query(default=None, ge=2000, le=2100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[BudgetRead]:
    stmt = select(Budget).where(Budget.user_id == current_user.id)
    if year is not None:
        stmt = stmt.where(Budget.year == year)
    stmt = stmt.order_by(desc(Budget.year), desc(Budget.month))
    rows = db.scalars(stmt).all()
    return [BudgetRead.model_validate(row) for row in rows]


@router.post("", response_model=BudgetRead, status_code=status.HTTP_201_CREATED)
def create_budget(payload: BudgetCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> BudgetRead:
    exists_stmt = select(Budget).where(Budget.user_id == current_user.id, Budget.year == payload.year, Budget.month == payload.month)
    if db.scalar(exists_stmt):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Budget already exists for this month")

    copied_from_id: int | None = None
    planned_amount: Decimal | None = payload.planned_amount

    if payload.copy_previous_month:
        prev_year, prev_month = _previous_year_month(payload.year, payload.month)
        prev_stmt = select(Budget).where(Budget.user_id == current_user.id, Budget.year == prev_year, Budget.month == prev_month)
        prev_budget = db.scalar(prev_stmt)
        if not prev_budget and planned_amount is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No previous month budget found to copy from")
        if prev_budget:
            copied_from_id = prev_budget.id
            if planned_amount is None:
                planned_amount = prev_budget.planned_amount

    if planned_amount is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="planned_amount is required")

    budget = Budget(
        user_id=current_user.id,
        year=payload.year,
        month=payload.month,
        planned_amount=planned_amount,
        copied_from_budget_id=copied_from_id,
    )
    db.add(budget)
    db.commit()
    db.refresh(budget)
    return BudgetRead.model_validate(budget)


@router.put("/{budget_id}", response_model=BudgetRead)
def update_budget(
    budget_id: int,
    payload: BudgetUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BudgetRead:
    budget = _get_budget_or_404(db, budget_id, current_user.id)

    budget.planned_amount = payload.planned_amount
    db.add(budget)
    db.commit()
    db.refresh(budget)
    return BudgetRead.model_validate(budget)


@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_budget(budget_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> None:
    budget = _get_budget_or_404(db, budget_id, current_user.id)
    db.delete(budget)
    db.commit()


@router.get("/{budget_id}/allocations", response_model=list[BudgetCategoryAllocationRead])
def list_budget_allocations(
    budget_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[BudgetCategoryAllocationRead]:
    _get_budget_or_404(db, budget_id, current_user.id)
    stmt = (
        select(BudgetCategoryAllocation, Category.name)
        .join(Category, Category.id == BudgetCategoryAllocation.category_id)
        .where(BudgetCategoryAllocation.budget_id == budget_id)
        .order_by(Category.name.asc())
    )
    rows = db.execute(stmt).all()
    return [
        BudgetCategoryAllocationRead(
            category_id=row[0].category_id,
            category_name=row[1],
            allocated_amount=row[0].allocated_amount,
        )
        for row in rows
    ]


@router.put("/{budget_id}/allocations", response_model=list[BudgetCategoryAllocationRead])
def set_budget_allocations(
    budget_id: int,
    payload: BudgetAllocationsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[BudgetCategoryAllocationRead]:
    budget = _get_budget_or_404(db, budget_id, current_user.id)

    hidden_category_exists = (
        select(UserHiddenCategory.id)
        .where(UserHiddenCategory.user_id == current_user.id, UserHiddenCategory.category_id == Category.id)
        .exists()
    )
    available_stmt = (
        select(Category.id)
        .where(or_(Category.user_id == current_user.id, Category.is_default.is_(True)))
        .where(~hidden_category_exists)
    )
    available_category_ids = set(db.scalars(available_stmt).all())

    total_allocated = Decimal("0")
    for item in payload.allocations:
        if item.category_id not in available_category_ids:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="One or more categories are not available")
        total_allocated += item.allocated_amount

    if total_allocated > budget.planned_amount:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Allocated amount exceeds monthly budget")

    existing_stmt = select(BudgetCategoryAllocation).where(BudgetCategoryAllocation.budget_id == budget_id)
    for row in db.scalars(existing_stmt).all():
        db.delete(row)
    db.flush()

    for item in payload.allocations:
        db.add(
            BudgetCategoryAllocation(
                budget_id=budget_id,
                category_id=item.category_id,
                allocated_amount=item.allocated_amount,
            )
        )

    db.commit()
    return list_budget_allocations(budget_id, db, current_user)
