"""Shared SQLAlchemy declarative base for all sequor models."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all ORM models. Provides metadata registry."""

    pass
