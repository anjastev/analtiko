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


class Signal(Base):
    __tablename__ = "signals"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    match_id = Column(
        Integer,
        ForeignKey("matches.id"),
        nullable=False,
        index=True,
    )

    market_id = Column(
        Integer,
        ForeignKey("markets.id"),
        nullable=False,
        index=True,
    )

    prediction_id = Column(
        Integer,
        ForeignKey("market_predictions.id"),
        nullable=True,
        index=True,
    )

    signal_type = Column(
        String,
        nullable=False,
    )

    selection = Column(
        String,
        nullable=False,
    )

    model_probability = Column(
        Float,
        nullable=False,
    )

    market_probability = Column(
        Float,
        nullable=True,
    )

    edge = Column(
        Float,
        nullable=True,
    )

    odds = Column(
        Float,
        nullable=True,
    )

    bookmaker = Column(
        String,
        nullable=True,
    )

    expected_value = Column(
        Float,
        nullable=True,
    )

    confidence_score = Column(
        Float,
        nullable=True,
    )

    risk_level = Column(
        String,
        nullable=True,
    )

    is_value = Column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
    )

    active = Column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
    )

    odds_recorded_at = Column(
        DateTime,
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