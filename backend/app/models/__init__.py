"""Every ORM model is imported here so Alembic autogenerate sees it."""

from app.models.base import Base

__all__ = ["Base"]
