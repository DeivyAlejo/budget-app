from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.payment_method import PaymentMethod

DEFAULT_CATEGORIES = [
    "Food",
    "Transportation",
    "Housing",
    "Utilities",
    "Health",
    "Entertainment",
    "Education",
    "Shopping",
    "Travel",
    "Other",
]

DEFAULT_PAYMENT_METHODS = [
    "Cash",
    "Debit Card",
    "Credit Card",
    "Bank Transfer",
    "Other",
]


def seed_defaults(db: Session) -> None:
    existing_categories = set(db.scalars(select(Category.name).where(Category.is_default.is_(True))).all())
    for name in DEFAULT_CATEGORIES:
        if name not in existing_categories:
            db.add(Category(name=name, user_id=None, is_default=True))

    existing_methods = set(db.scalars(select(PaymentMethod.name).where(PaymentMethod.is_default.is_(True))).all())
    for name in DEFAULT_PAYMENT_METHODS:
        if name not in existing_methods:
            db.add(PaymentMethod(name=name, user_id=None, is_default=True))

    db.commit()
