from pydantic import BaseModel, field_validator

from app.urls import normalize_url


def normalize_tag(tag: str) -> str:
    return tag.strip().lower()


class BookmarkCreate(BaseModel):
    url: str
    title: str | None = None
    tags: list[str] = []

    @field_validator("url")
    @classmethod
    def _normalize_url(cls, value: str) -> str:
        return normalize_url(value)

    @field_validator("tags")
    @classmethod
    def _normalize_tags(cls, value: list[str]) -> list[str]:
        cleaned = (normalize_tag(tag) for tag in value)
        return list(dict.fromkeys(tag for tag in cleaned if tag))


class BookmarkOut(BaseModel):
    id: int
    url: str
    title: str | None
    tags: list[str]
    created_at: str
