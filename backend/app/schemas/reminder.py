from decimal import Decimal

from pydantic import BaseModel


class ReminderCard(BaseModel):
    reminder_type: str  # "missing_budget", "missing_recurring", "over_allocation", "near_allocation"
    title: str
    message: str
    severity: str  # "info", "warning", "alert"
    action_url: str | None = None  # URL hint for UI to navigate


class RemindersResponse(BaseModel):
    year: int
    month: int
    cards: list[ReminderCard]
