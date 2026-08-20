from sqlalchemy import (
    Boolean,
    Column,
    Integer,
    String,
)

from app.database.database import Base


class Market(Base):
    __tablename__ = "markets"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    sport = Column(
        String,
        nullable=False,
        index=True,
    )

    code = Column(
        String,
        nullable=False,
        index=True,
    )

    name = Column(
        String,
        nullable=False,
    )

    category = Column(
        String,
        nullable=False,
    )

    enabled = Column(
        Boolean,
        default=True,
        nullable=False,
    )