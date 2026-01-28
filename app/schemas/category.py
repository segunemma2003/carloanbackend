"""
Category schemas.
"""

from typing import Optional, List

from pydantic import BaseModel, Field

from app.schemas.common import BaseSchema


class CategoryBase(BaseModel):
    """Base category fields."""

    name: str = Field(..., min_length=1, max_length=100)
    slug: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    icon: Optional[str] = None
    image_url: Optional[str] = None
    parent_id: Optional[int] = None
    sort_order: int = 0
    is_active: bool = True
    show_in_menu: bool = True
    
    # SEO
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None
    seo_h1: Optional[str] = None
    seo_text: Optional[str] = None


class CategoryCreate(CategoryBase):
    """Create category schema."""
    pass


class CategoryUpdate(BaseModel):
    """Update category schema."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    slug: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    icon: Optional[str] = None
    image_url: Optional[str] = None
    parent_id: Optional[int] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None
    show_in_menu: Optional[bool] = None
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None
    seo_h1: Optional[str] = None
    seo_text: Optional[str] = None


class CategoryResponse(BaseSchema):
    """Category response."""

    id: int
    name: str
    slug: str
    description: Optional[str] = None
    icon: Optional[str] = None
    image_url: Optional[str] = None
    parent_id: Optional[int] = None
    level: int
    sort_order: int
    is_active: bool
    show_in_menu: bool
    ads_count: int
    
    # SEO
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None
    seo_h1: Optional[str] = None
    seo_text: Optional[str] = None


class CategoryWithChildren(CategoryResponse):
    """Category with nested children."""

    children: List["CategoryWithChildren"] = []


class CategoryTree(BaseModel):
    """Full category tree for menu."""

    categories: List[CategoryWithChildren]


# Required for self-referencing model
CategoryWithChildren.model_rebuild()

