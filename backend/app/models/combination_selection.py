from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
)

from app.database.database import Base


class CombinationSelection(Base):
    __tablename__ = "combination_selections"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    combination_id = Column(
        Integer,
        ForeignKey("combinations.id"),
        nullable=False,
        index=True,
    )

    signal_id = Column(
        Integer,
        ForeignKey("signals.id"),
        nullable=False,
        index=True,
    )

    match_id = Column(
        Integer,
        ForeignKey("matches.id"),
        nullable=False,
        index=True,
    )

    selection = Column(
        String,
        nullable=False,
    )

    odds = Column(
        Float,
        nullable=True,
    )

    probability = Column(
        Float,
        nullable=True,
    )

    correlation_group = Column(
        String,
        nullable=True,
    )

    actual_result = Column(
        String,
        nullable=True,
    )

    correct = Column(
        Boolean,
        nullable=True,
    )

    profit = Column(
        Float,
        nullable=True,
    )

    evaluated_at = Column(
        DateTime,
        nullable=True,
    )