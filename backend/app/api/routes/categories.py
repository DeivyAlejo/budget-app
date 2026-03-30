from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import exists, or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.category import Category
from app.models.user import User
from app.models.user_hidden_category import UserHiddenCategory
from app.schemas.category import CategoryCreate, CategoryRead, CategoryUpdate

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[CategoryRead])
def list_categories(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> list[CategoryRead]:
    hidden_subquery = (
        select(UserHiddenCategory.id)
        .where(UserHiddenCategory.user_id == current_user.id, UserHiddenCategory.category_id == Category.id)
        .exists()
    )
    stmt = (
        select(Category)
        .where(or_(Category.user_id == current_user.id, Category.is_default.is_(True)))
        .where(~hidden_subquery)
        .order_by(Category.is_default.desc(), Category.name.asc())
    )
    categories = db.scalars(stmt).all()
    return [CategoryRead.model_validate(item) for item in categories]


@router.post("", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
def create_category(payload: CategoryCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> CategoryRead:
    normalized = payload.name.strip()
    existing_stmt = select(Category).where(Category.user_id == current_user.id, Category.name.ilike(normalized))
    if db.scalar(existing_stmt):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Category already exists")

    category = Category(name=normalized, user_id=current_user.id, is_default=False)
    db.add(category)
    db.commit()
    db.refresh(category)
    return CategoryRead.model_validate(category)


@router.put("/{category_id}", response_model=CategoryRead)
def update_category(
    category_id: int,
    payload: CategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CategoryRead:
    category = db.get(Category, category_id)
    if not category or category.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    category.name = payload.name.strip()
    db.add(category)
    db.commit()
    db.refresh(category)
    return CategoryRead.model_validate(category)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> None:
    category = db.get(Category, category_id)
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    if category.user_id == current_user.id:
        db.delete(category)
        db.commit()
        return

    if category.is_default:
        exists_stmt = select(UserHiddenCategory).where(
            UserHiddenCategory.user_id == current_user.id,
            UserHiddenCategory.category_id == category.id,
        )
        if not db.scalar(exists_stmt):
            db.add(UserHiddenCategory(user_id=current_user.id, category_id=category.id))
            db.commit()
        return

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
