from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Integer,
    String,
)

from app.database.database import Base


class Combination(Base):
    __tablename__ = "combinations"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    name = Column(
        String,
        nullable=False,
    )

    strategy = Column(
        String,
        nullable=False,
        index=True,
    )

    sport = Column(
        String,
        nullable=False,
        index=True,
    )

    total_odds = Column(
        Float,
        nullable=True,
    )

    estimated_probability = Column(
        Float,
        nullable=True,
    )

    risk_score = Column(
        Float,
        nullable=True,
    )

    status = Column(
        String,
        default="pending",
        nullable=False,
        index=True,
    )

    signature = Column(
        String,
        nullable=True,
        index=True,
    )

    profit = Column(
        Float,
        nullable=True,
    )

    roi = Column(
        Float,
        nullable=True,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True,
    )

    evaluated_at = Column(
        DateTime,
        nullable=True,
    )