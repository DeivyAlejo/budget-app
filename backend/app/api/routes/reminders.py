from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, extract, func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.budget import Budget
from app.models.budget_category_allocation import BudgetCategoryAllocation
from app.models.expense import Expense
from app.models.recurring_template import RecurringTemplate
from app.models.user import User
from app.schemas.reminder import ReminderCard, RemindersResponse

router = APIRouter(prefix="/reminders", tags=["reminders"])


@router.get("", response_model=RemindersResponse)
def get_reminders(
    year: int = Query(ge=2000, le=2100),
    month: int = Query(ge=1, le=12),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RemindersResponse:
    """Get reminder cards for a specific month."""
    cards: list[ReminderCard] = []

    # 1. Check if budget exists for this month
    budget_stmt = select(Budget).where(
        and_(
            Budget.user_id == current_user.id,
            Budget.year == year,
            Budget.month == month,
        )
    )
    budget = db.scalar(budget_stmt)

    if not budget:
        cards.append(
            ReminderCard(
                reminder_type="missing_budget",
                title="Budget Not Created",
                message=f"No budget created for {year}-{month:02d}. Create one to track spending.",
                severity="info",
                action_url=f"/dashboard?year={year}&month={month}",
            )
        )

    # 2. Check if active recurring templates have been generated for this month
    active_templates_stmt = select(RecurringTemplate).where(
        and_(
            RecurringTemplate.user_id == current_user.id,
            RecurringTemplate.is_active.is_(True),
        )
    )
    active_templates = db.scalars(active_templates_stmt).all()

    pending_templates = [
        t
        for t in active_templates
        if t.last_generated_year is None or t.last_generated_year != year or t.last_generated_month != month
    ]

    if pending_templates:
        cards.append(
            ReminderCard(
                reminder_type="missing_recurring",
                title=f"{len(pending_templates)} Recurring Expense(s) Pending",
                message=f"Generate {len(pending_templates)} active recurring template(s) for this month.",
                severity="warning",
                action_url=f"/dashboard?year={year}&month={month}#recurring",
            )
        )

    # 3. Check allocations for over/near-allocation if budget exists
    if budget:
        allocations_stmt = select(BudgetCategoryAllocation).where(
            BudgetCategoryAllocation.budget_id == budget.id
        )
        allocations = db.scalars(allocations_stmt).all()

        for allocation in allocations:
            # Sum expenses for this category in this month
            expense_sum_stmt = select(func.coalesce(func.sum(Expense.amount), Decimal("0"))).where(
                and_(
                    Expense.user_id == current_user.id,
                    Expense.category_id == allocation.category_id,
                    extract("year", Expense.spent_at) == year,
                    extract("month", Expense.spent_at) == month,
                )
            )
            spent = db.scalar(expense_sum_stmt) or Decimal("0")

            allocation_amount = allocation.allocated_amount
            if spent > allocation_amount:
                overage = spent - allocation_amount
                cards.append(
                    ReminderCard(
                        reminder_type="over_allocation",
                        title="Over Budget",
                        message=f"Category exceeded allocation by ${overage:.2f}. Spent: ${spent:.2f}, Allocated: ${allocation_amount:.2f}.",
                        severity="alert",
                        action_url=f"/dashboard?year={year}&month={month}&category={allocation.category_id}",
                    )
                )
            elif spent > allocation_amount * Decimal("0.8"):  # 80% threshold
                remaining = allocation_amount - spent
                cards.append(
                    ReminderCard(
                        reminder_type="near_allocation",
                        title="Approaching Budget",
                        message=f"Category at 80%+ of allocation. Remaining: ${remaining:.2f}.",
                        severity="warning",
                        action_url=f"/dashboard?year={year}&month={month}&category={allocation.category_id}",
                    )
                )

    return RemindersResponse(year=year, month=month, cards=cards)
