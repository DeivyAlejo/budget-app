from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.payment_method import PaymentMethod
from app.models.user import User
from app.models.user_hidden_payment_method import UserHiddenPaymentMethod
from app.schemas.payment_method import PaymentMethodCreate, PaymentMethodRead, PaymentMethodUpdate

router = APIRouter(prefix="/payment-methods", tags=["payment-methods"])


@router.get("", response_model=list[PaymentMethodRead])
def list_payment_methods(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> list[PaymentMethodRead]:
    hidden_subquery = (
        select(UserHiddenPaymentMethod.id)
        .where(
            UserHiddenPaymentMethod.user_id == current_user.id,
            UserHiddenPaymentMethod.payment_method_id == PaymentMethod.id,
        )
        .exists()
    )
    stmt = (
        select(PaymentMethod)
        .where(or_(PaymentMethod.user_id == current_user.id, PaymentMethod.is_default.is_(True)))
        .where(~hidden_subquery)
        .order_by(PaymentMethod.is_default.desc(), PaymentMethod.name.asc())
    )
    methods = db.scalars(stmt).all()
    return [PaymentMethodRead.model_validate(item) for item in methods]


@router.post("", response_model=PaymentMethodRead, status_code=status.HTTP_201_CREATED)
def create_payment_method(
    payload: PaymentMethodCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PaymentMethodRead:
    normalized = payload.name.strip()
    existing_stmt = select(PaymentMethod).where(PaymentMethod.user_id == current_user.id, PaymentMethod.name.ilike(normalized))
    if db.scalar(existing_stmt):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Payment method already exists")

    method = PaymentMethod(name=normalized, user_id=current_user.id, is_default=False)
    db.add(method)
    db.commit()
    db.refresh(method)
    return PaymentMethodRead.model_validate(method)


@router.put("/{payment_method_id}", response_model=PaymentMethodRead)
def update_payment_method(
    payment_method_id: int,
    payload: PaymentMethodUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PaymentMethodRead:
    method = db.get(PaymentMethod, payment_method_id)
    if not method or method.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment method not found")

    method.name = payload.name.strip()
    db.add(method)
    db.commit()
    db.refresh(method)
    return PaymentMethodRead.model_validate(method)


@router.delete("/{payment_method_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_payment_method(payment_method_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> None:
    method = db.get(PaymentMethod, payment_method_id)
    if not method:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment method not found")

    if method.user_id == current_user.id:
        db.delete(method)
        db.commit()
        return

    if method.is_default:
        exists_stmt = select(UserHiddenPaymentMethod).where(
            UserHiddenPaymentMethod.user_id == current_user.id,
            UserHiddenPaymentMethod.payment_method_id == method.id,
        )
        if not db.scalar(exists_stmt):
            db.add(UserHiddenPaymentMethod(user_id=current_user.id, payment_method_id=method.id))
            db.commit()
        return

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment method not found")
