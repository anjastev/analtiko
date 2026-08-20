from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    String,
)

from sqlalchemy.sql import func

from app.database.database import Base


class DataSource(Base):
    __tablename__ = "data_sources"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    name = Column(
        String,
        unique=True,
        nullable=False,
        index=True,
    )

    provider_type = Column(
        String,
        nullable=False,
    )

    sport = Column(
        String,
        nullable=True,
    )

    base_url = Column(
        String,
        nullable=True,
    )

    enabled = Column(
        Boolean,
        default=True,
        nullable=False,
    )

    priority = Column(
        Integer,
        default=100,
        nullable=False,
    )

    created_at = Column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )