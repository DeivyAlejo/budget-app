from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import extract, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.income import Income
from app.models.user import User
from app.schemas.income import IncomeCreate, IncomeRead, IncomeUpdate

router = APIRouter(prefix="/income", tags=["income"])


@router.post("", response_model=IncomeRead, status_code=status.HTTP_201_CREATED)
def create_income(
    payload: IncomeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> IncomeRead:
    income = Income(
        user_id=current_user.id,
        description=payload.description.strip(),
        amount=payload.amount,
        income_type=payload.income_type,
        received_at=payload.received_at,
    )
    db.add(income)
    db.commit()
    db.refresh(income)
    return IncomeRead.model_validate(income)


@router.get("", response_model=list[IncomeRead])
def list_income(
    year: int,
    month: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[IncomeRead]:
    stmt = (
        select(Income)
        .where(
            Income.user_id == current_user.id,
            extract("year", Income.received_at) == year,
            extract("month", Income.received_at) == month,
        )
        .order_by(Income.received_at.desc())
    )
    rows = db.execute(stmt).scalars().all()
    return [IncomeRead.model_validate(row) for row in rows]


@router.put("/{income_id}", response_model=IncomeRead)
def update_income(
    income_id: int,
    payload: IncomeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> IncomeRead:
    income = db.get(Income, income_id)
    if not income or income.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Income not found")

    income.description = payload.description.strip()
    income.amount = payload.amount
    income.income_type = payload.income_type
    income.received_at = payload.received_at

    db.add(income)
    db.commit()
    db.refresh(income)
    return IncomeRead.model_validate(income)


@router.delete("/{income_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_income(
    income_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    income = db.get(Income, income_id)
    if not income or income.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Income not found")
    db.delete(income)
    db.commit()
