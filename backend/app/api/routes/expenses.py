from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import extract, or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.category import Category
from app.models.expense import Expense
from app.models.payment_method import PaymentMethod
from app.models.user import User
from app.models.user_hidden_category import UserHiddenCategory
from app.models.user_hidden_payment_method import UserHiddenPaymentMethod
from app.schemas.expense import ExpenseCreate, ExpenseRead, ExpenseUpdate

router = APIRouter(prefix="/expenses", tags=["expenses"])


def _validate_category_access(db: Session, user_id: int, category_id: int) -> None:
    hidden_stmt = select(UserHiddenCategory).where(UserHiddenCategory.user_id == user_id, UserHiddenCategory.category_id == category_id)
    if db.scalar(hidden_stmt):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    stmt = select(Category).where(Category.id == category_id, or_(Category.is_default.is_(True), Category.user_id == user_id))
    if not db.scalar(stmt):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")


def _validate_payment_method_access(db: Session, user_id: int, payment_method_id: int) -> None:
    hidden_stmt = select(UserHiddenPaymentMethod).where(
        UserHiddenPaymentMethod.user_id == user_id,
        UserHiddenPaymentMethod.payment_method_id == payment_method_id,
    )
    if db.scalar(hidden_stmt):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment method not found")

    stmt = select(PaymentMethod).where(
        PaymentMethod.id == payment_method_id,
        or_(PaymentMethod.is_default.is_(True), PaymentMethod.user_id == user_id),
    )
    if not db.scalar(stmt):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment method not found")


@router.post("", response_model=ExpenseRead, status_code=status.HTTP_201_CREATED)
def create_expense(payload: ExpenseCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> ExpenseRead:
    _validate_category_access(db, current_user.id, payload.category_id)
    _validate_payment_method_access(db, current_user.id, payload.payment_method_id)

    expense = Expense(
        user_id=current_user.id,
        category_id=payload.category_id,
        payment_method_id=payload.payment_method_id,
        description=payload.description.strip(),
        amount=payload.amount,
        spent_at=payload.spent_at,
        is_recurring=payload.is_recurring,
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return ExpenseRead.model_validate(expense)


@router.get("", response_model=list[ExpenseRead])
def list_expenses(
    year: int | None = Query(default=None, ge=2000, le=2100),
    month: int | None = Query(default=None, ge=1, le=12),
    category_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ExpenseRead]:
    stmt = select(Expense).where(Expense.user_id == current_user.id)
    if year is not None:
        stmt = stmt.where(extract("year", Expense.spent_at) == year)
    if month is not None:
        stmt = stmt.where(extract("month", Expense.spent_at) == month)
    if category_id is not None:
        stmt = stmt.where(Expense.category_id == category_id)

    expenses = db.scalars(stmt.order_by(Expense.spent_at.desc(), Expense.id.desc())).all()
    return [ExpenseRead.model_validate(item) for item in expenses]


@router.put("/{expense_id}", response_model=ExpenseRead)
def update_expense(
    expense_id: int,
    payload: ExpenseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ExpenseRead:
    expense = db.get(Expense, expense_id)
    if not expense or expense.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")

    _validate_category_access(db, current_user.id, payload.category_id)
    _validate_payment_method_access(db, current_user.id, payload.payment_method_id)

    expense.category_id = payload.category_id
    expense.payment_method_id = payload.payment_method_id
    expense.description = payload.description.strip()
    expense.amount = payload.amount
    expense.spent_at = payload.spent_at
    expense.is_recurring = payload.is_recurring

    db.add(expense)
    db.commit()
    db.refresh(expense)
    return ExpenseRead.model_validate(expense)


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(expense_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> None:
    expense = db.get(Expense, expense_id)
    if not expense or expense.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")

    db.delete(expense)
    db.commit()
