from sqlalchemy import (
    Boolean,
    Column,
    Integer,
    String,
)

from app.database.database import Base


class Sport(Base):
    __tablename__ = "sports"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    code = Column(
        String,
        unique=True,
        nullable=False,
        index=True,
    )

    name = Column(
        String,
        unique=True,
        nullable=False,
    )

    enabled = Column(
        Boolean,
        default=True,
        nullable=False,
    )