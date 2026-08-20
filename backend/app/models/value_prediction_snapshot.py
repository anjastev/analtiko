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


class ValuePredictionSnapshot(Base):

    __tablename__ = "value_prediction_snapshots"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    match_id = Column(
        Integer,
        ForeignKey(
            "matches.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    model_version = Column(
        String,
        nullable=False,
        default="logistic_regression_v2",
    )

    bookmaker = Column(
        String,
        nullable=True,
    )

    value_pick = Column(
        String,
        nullable=False,
    )

    model_pick = Column(
        String,
        nullable=False,
    )

    model_probability = Column(
        Float,
        nullable=False,
    )

    market_probability = Column(
        Float,
        nullable=False,
    )

    edge = Column(
        Float,
        nullable=False,
    )

    market_odds = Column(
        Float,
        nullable=False,
    )

    fair_odds = Column(
        Float,
        nullable=True,
    )

    expected_value = Column(
        Float,
        nullable=True,
    )

    analitiko_score = Column(
        Float,
        nullable=False,
        default=0.0,
    )

    ml_confidence = Column(
        Float,
        nullable=False,
        default=0.0,
    )

    is_strong_pick = Column(
        Boolean,
        nullable=False,
        default=False,
    )

    is_elite_pick = Column(
        Boolean,
        nullable=False,
        default=False,
    )

    is_value_pick = Column(
        Boolean,
        nullable=False,
        default=True,
    )

    is_elite_value = Column(
        Boolean,
        nullable=False,
        default=False,
    )

    same_as_model_pick = Column(
        Boolean,
        nullable=False,
        default=False,
    )

    odds_recorded_at = Column(
        DateTime,
        nullable=True,
    )

    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        index=True,
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

    evaluated_at = Column(
        DateTime,
        nullable=True,
    )