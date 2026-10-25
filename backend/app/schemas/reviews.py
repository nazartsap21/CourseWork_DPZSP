from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from ..models import Review

ReviewText = Annotated[str, StringConstraints(strip_whitespace=True, max_length=1000)]


class ReviewIn(BaseModel):
    rating: int = Field(ge=1, le=5)
    text: ReviewText = ""


class OwnReviewOut(BaseModel):
    """The customer's own review, shown on their order."""

    model_config = ConfigDict(from_attributes=True)

    rating: int
    text: str
    created_at: datetime


class PublicReviewOut(BaseModel):
    """A review on the restaurant page; the author appears as first name + initial."""

    id: int
    rating: int
    text: str
    author: str
    created_at: datetime

    @classmethod
    def from_review(cls, review: Review) -> "PublicReviewOut":
        parts = review.customer.name.split()
        author = parts[0] if len(parts) == 1 else f"{parts[0]} {parts[-1][0]}."
        return cls(
            id=review.id,
            rating=review.rating,
            text=review.text,
            author=author,
            created_at=review.created_at,
        )
