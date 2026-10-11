from pydantic import BaseModel, Field


class PageParams(BaseModel):
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=12, ge=1, le=50)


class Page[ItemT](BaseModel):
    items: list[ItemT]
    total: int
    page: int
    per_page: int
    pages: int
