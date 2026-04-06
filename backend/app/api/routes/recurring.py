from datetime import datetime, timezone, date
from calendar import monthrange

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.category import Category
from app.models.expense import Expense
from app.models.payment_method import PaymentMethod
from app.models.recurring_template import RecurringTemplate
from app.models.user import User
from app.models.user_hidden_category import UserHiddenCategory
from app.models.user_hidden_payment_method import UserHiddenPaymentMethod
from app.schemas.recurring import (
    GenerationSummary,
    RecurringTemplateCreate,
    RecurringTemplateRead,
    RecurringTemplateUpdate,
)

router = APIRouter(prefix="/recurring-expenses", tags=["recurring-expenses"])


def _validate_category_access(db: Session, user_id: int, category_id: int) -> None:
    hidden_stmt = select(UserHiddenCategory).where(
        UserHiddenCategory.user_id == user_id, UserHiddenCategory.category_id == category_id
    )
    if db.scalar(hidden_stmt):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    stmt = select(Category).where(
        Category.id == category_id, or_(Category.is_default.is_(True), Category.user_id == user_id)
    )
    if not db.scalar(stmt):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")


def _validate_payment_method_access(db: Session, user_id: int, payment_method_id: int) -> None:
    hidden_stmt = select(UserHiddenPaymentMethod).where(
        UserHiddenPaymentMethod.user_id == user_id, UserHiddenPaymentMethod.payment_method_id == payment_method_id
    )
    if db.scalar(hidden_stmt):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment method not found")

    stmt = select(PaymentMethod).where(
        PaymentMethod.id == payment_method_id,
        or_(PaymentMethod.is_default.is_(True), PaymentMethod.user_id == user_id),
    )
    if not db.scalar(stmt):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment method not found")


def _clamp_day_to_month(day: int, year: int, month: int) -> int:
    """Clamp day to last day of month. E.g., day 31 in February becomes 28 (or 29 in leap years)."""
    _, last_day = monthrange(year, month)
    return min(day, last_day)


@router.post("", response_model=RecurringTemplateRead, status_code=status.HTTP_201_CREATED)
def create_recurring_template(
    payload: RecurringTemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RecurringTemplateRead:
    """Create a new recurring expense template."""
    _validate_category_access(db, current_user.id, payload.category_id)
    _validate_payment_method_access(db, current_user.id, payload.payment_method_id)

    template = RecurringTemplate(
        user_id=current_user.id,
        category_id=payload.category_id,
        payment_method_id=payload.payment_method_id,
        description=payload.description.strip(),
        amount=payload.amount,
        day_of_month=payload.day_of_month,
        frequency=payload.frequency,
        is_active=payload.is_active,
        notes=payload.notes.strip() if payload.notes else None,
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return RecurringTemplateRead.model_validate(template)


@router.get("", response_model=list[RecurringTemplateRead])
def list_recurring_templates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[RecurringTemplateRead]:
    """List all recurring templates for the current user."""
    stmt = select(RecurringTemplate).where(RecurringTemplate.user_id == current_user.id).order_by(RecurringTemplate.created_at.desc())
    templates = db.scalars(stmt).all()
    return [RecurringTemplateRead.model_validate(item) for item in templates]


@router.get("/{template_id}", response_model=RecurringTemplateRead)
def get_recurring_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RecurringTemplateRead:
    """Get a specific recurring template by ID."""
    template = db.get(RecurringTemplate, template_id)
    if not template or template.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    return RecurringTemplateRead.model_validate(template)


@router.put("/{template_id}", response_model=RecurringTemplateRead)
def update_recurring_template(
    template_id: int,
    payload: RecurringTemplateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RecurringTemplateRead:
    """Update a recurring template. Only affects future generation."""
    template = db.get(RecurringTemplate, template_id)
    if not template or template.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")

    # Validate access if category/payment method is being changed
    if payload.category_id is not None:
        _validate_category_access(db, current_user.id, payload.category_id)
        template.category_id = payload.category_id
    if payload.payment_method_id is not None:
        _validate_payment_method_access(db, current_user.id, payload.payment_method_id)
        template.payment_method_id = payload.payment_method_id

    if payload.description is not None:
        template.description = payload.description.strip()
    if payload.amount is not None:
        template.amount = payload.amount
    if payload.day_of_month is not None:
        template.day_of_month = payload.day_of_month
    if payload.frequency is not None:
        template.frequency = payload.frequency
    if payload.is_active is not None:
        template.is_active = payload.is_active
    if payload.notes is not None:
        template.notes = payload.notes.strip() if payload.notes else None

    template.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(template)
    return RecurringTemplateRead.model_validate(template)


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_recurring_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete a recurring template. Does not affect already generated expenses."""
    template = db.get(RecurringTemplate, template_id)
    if not template or template.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")

    db.delete(template)
    db.commit()


@router.post("/{template_id}/generate", response_model=GenerationSummary)
def generate_recurring_expense(
    template_id: int,
    year: int = Query(ge=2000, le=2100),
    month: int = Query(ge=1, le=12),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> GenerationSummary:
    """Generate a single recurring expense for a specific month. Idempotent—skip if already generated."""
    template = db.get(RecurringTemplate, template_id)
    if not template or template.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")

    if not template.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Template is inactive")

    # Check if already generated for this month
    clamped_day = _clamp_day_to_month(template.day_of_month, year, month)
    spent_date = date(year, month, clamped_day)
    
    existing_stmt = select(Expense).where(
        and_(
            Expense.user_id == current_user.id,
            Expense.category_id == template.category_id,
            Expense.payment_method_id == template.payment_method_id,
            Expense.description == template.description,
            Expense.amount == template.amount,
            Expense.spent_at == spent_date,
        )
    )

    if db.scalar(existing_stmt):
        # Already generated; return summary with count=0
        return GenerationSummary(
            template_id=template_id,
            created_count=0,
            total_amount=template.amount,
            year=year,
            month=month,
        )

    # Create the expense
    expense = Expense(
        user_id=current_user.id,
        category_id=template.category_id,
        payment_method_id=template.payment_method_id,
        description=template.description,
        amount=template.amount,
        spent_at=spent_date,
        is_recurring=True,
    )
    db.add(expense)

    # Update template's last_generated tracking
    template.last_generated_year = year
    template.last_generated_month = month

    db.commit()
    return GenerationSummary(
        template_id=template_id,
        created_count=1,
        total_amount=template.amount,
        year=year,
        month=month,
    )


@router.post("/batch/generate", response_model=list[GenerationSummary])
def generate_all_recurring_expenses(
    year: int = Query(ge=2000, le=2100),
    month: int = Query(ge=1, le=12),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[GenerationSummary]:
    """Generate all active recurring templates for a specific month. Idempotent."""
    templates_stmt = select(RecurringTemplate).where(
        and_(RecurringTemplate.user_id == current_user.id, RecurringTemplate.is_active.is_(True))
    )
    templates = db.scalars(templates_stmt).all()

    summaries = []
    for template in templates:
        summary = generate_recurring_expense(template.id, year, month, db, current_user)
        summaries.append(summary)

    return summaries
