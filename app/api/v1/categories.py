"""
Category endpoints.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.exceptions import NotFoundError, ConflictError
from app.models.category import Category
from app.models.user import User
from app.schemas.category import (
    CategoryResponse,
    CategoryCreate,
    CategoryUpdate,
    CategoryWithChildren,
    CategoryTree,
)
from app.schemas.common import MessageOut
from app.api.deps import get_current_user, require_admin


router = APIRouter()


async def build_category_tree(
    categories: List[Category],
    parent_id: int = None,
) -> List[CategoryWithChildren]:
    """Build nested category tree."""
    result = []
    for cat in categories:
        if cat.parent_id == parent_id:
            children = await build_category_tree(categories, cat.id)
            cat_response = CategoryWithChildren.model_validate(cat)
            cat_response.children = children
            result.append(cat_response)
    return result


@router.get("/", response_model=List[CategoryResponse])
async def list_categories(
    parent_id: int = None,
    include_inactive: bool = False,
    db: AsyncSession = Depends(get_db),
):
    """
    List categories.
    
    - Filter by parent_id for subcategories
    - By default only returns active categories
    """
    query = select(Category)

    if parent_id is not None:
        query = query.where(Category.parent_id == parent_id)
    else:
        # Top-level categories only if no parent specified
        query = query.where(Category.parent_id.is_(None))

    if not include_inactive:
        query = query.where(Category.is_active == True)

    query = query.order_by(Category.sort_order, Category.name)

    result = await db.execute(query)
    categories = result.scalars().all()

    return [CategoryResponse.model_validate(c) for c in categories]


@router.get("/tree", response_model=CategoryTree)
async def get_category_tree(
    db: AsyncSession = Depends(get_db),
):
    """
    Get full category tree for navigation menu.
    """
    result = await db.execute(
        select(Category).where(
            Category.is_active == True,
            Category.show_in_menu == True,
        ).order_by(Category.sort_order, Category.name)
    )
    categories = result.scalars().all()

    tree = await build_category_tree(list(categories))

    return CategoryTree(categories=tree)


@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(
    category_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Get category by ID.
    """
    result = await db.execute(
        select(Category).where(Category.id == category_id)
    )
    category = result.scalar_one_or_none()

    if not category:
        raise NotFoundError("Category not found", "category", category_id)

    return CategoryResponse.model_validate(category)


@router.get("/slug/{slug}", response_model=CategoryResponse)
async def get_category_by_slug(
    slug: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get category by slug.
    """
    result = await db.execute(
        select(Category).where(Category.slug == slug)
    )
    category = result.scalar_one_or_none()

    if not category:
        raise NotFoundError("Category not found", "category", slug)

    return CategoryResponse.model_validate(category)


# Admin endpoints

@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    category_data: CategoryCreate,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    """
    Create new category (admin only).
    """
    # Check slug uniqueness
    result = await db.execute(
        select(Category).where(Category.slug == category_data.slug)
    )
    if result.scalar_one_or_none():
        raise ConflictError("Category with this slug already exists")

    # Check parent exists
    if category_data.parent_id:
        result = await db.execute(
            select(Category).where(Category.id == category_data.parent_id)
        )
        parent = result.scalar_one_or_none()
        if not parent:
            raise NotFoundError("Parent category not found", "category", category_data.parent_id)
        level = parent.level + 1
    else:
        level = 0

    category = Category(
        **category_data.model_dump(),
        level=level,
    )
    db.add(category)
    await db.commit()
    await db.refresh(category)

    return CategoryResponse.model_validate(category)


@router.patch("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: int,
    update_data: CategoryUpdate,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    """
    Update category (admin only).
    """
    result = await db.execute(
        select(Category).where(Category.id == category_id)
    )
    category = result.scalar_one_or_none()

    if not category:
        raise NotFoundError("Category not found", "category", category_id)

    update_dict = update_data.model_dump(exclude_unset=True)

    # Check slug uniqueness if updating
    if "slug" in update_dict:
        result = await db.execute(
            select(Category).where(
                Category.slug == update_dict["slug"],
                Category.id != category_id,
            )
        )
        if result.scalar_one_or_none():
            raise ConflictError("Category with this slug already exists")

    # Update parent and level
    if "parent_id" in update_dict:
        if update_dict["parent_id"]:
            result = await db.execute(
                select(Category).where(Category.id == update_dict["parent_id"])
            )
            parent = result.scalar_one_or_none()
            if not parent:
                raise NotFoundError("Parent category not found")
            update_dict["level"] = parent.level + 1
        else:
            update_dict["level"] = 0

    for field, value in update_dict.items():
        setattr(category, field, value)

    await db.commit()
    await db.refresh(category)

    return CategoryResponse.model_validate(category)


@router.delete("/{category_id}", response_model=MessageOut)
async def delete_category(
    category_id: int,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    """
    Delete category (admin only).
    Also deletes all subcategories.
    """
    result = await db.execute(
        select(Category).where(Category.id == category_id)
    )
    category = result.scalar_one_or_none()

    if not category:
        raise NotFoundError("Category not found", "category", category_id)

    await db.delete(category)
    await db.commit()

    return MessageOut(message="Category deleted successfully")

