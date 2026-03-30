from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import extract, func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.category import Category
from app.models.expense import Expense
from app.models.user import User
from app.schemas.report import CategoryExpensesReport, CategoryTotal, ExpenseLine

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/categories/totals", response_model=list[CategoryTotal])
def category_totals(
    year: int = Query(ge=2000, le=2100),
    month: int | None = Query(default=None, ge=1, le=12),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[CategoryTotal]:
    stmt = (
        select(Category.id, Category.name, func.coalesce(func.sum(Expense.amount), 0))
        .join(Category, Category.id == Expense.category_id)
        .where(Expense.user_id == current_user.id)
        .where(extract("year", Expense.spent_at) == year)
        .group_by(Category.id, Category.name)
        .order_by(func.sum(Expense.amount).desc())
    )

    if month is not None:
        stmt = stmt.where(extract("month", Expense.spent_at) == month)

    rows = db.execute(stmt).all()
    return [CategoryTotal(category_id=row[0], category_name=row[1], total_amount=Decimal(row[2])) for row in rows]


@router.get("/categories/{category_id}", response_model=CategoryExpensesReport)
def category_detail(
    category_id: int,
    year: int = Query(ge=2000, le=2100),
    month: int | None = Query(default=None, ge=1, le=12),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CategoryExpensesReport:
    category = db.get(Category, category_id)
    if not category:
        return CategoryExpensesReport(category_id=category_id, category_name="Unknown", total_amount=Decimal("0"), expenses=[])

    stmt = select(Expense).where(Expense.user_id == current_user.id, Expense.category_id == category_id)
    stmt = stmt.where(extract("year", Expense.spent_at) == year)
    if month is not None:
        stmt = stmt.where(extract("month", Expense.spent_at) == month)

    expenses = db.scalars(stmt.order_by(Expense.spent_at.desc(), Expense.id.desc())).all()
    total = sum((item.amount for item in expenses), Decimal("0"))

    lines = [
        ExpenseLine(expense_id=item.id, description=item.description, amount=item.amount, spent_at=item.spent_at).model_dump()
        for item in expenses
    ]

    return CategoryExpensesReport(
        category_id=category.id,
        category_name=category.name,
        total_amount=total,
        expenses=lines,
    )
