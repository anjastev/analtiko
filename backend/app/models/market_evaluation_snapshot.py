from datetime import (
    datetime,
    timezone,
)

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


class MarketEvaluationSnapshot(Base):

    __tablename__ = (
        "market_evaluation_snapshots"
    )

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    match_id = Column(
        Integer,
        ForeignKey(
            "matches.id"
        ),
        nullable=False,
        index=True,
    )

    market_id = Column(
        Integer,
        ForeignKey(
            "markets.id"
        ),
        nullable=False,
        index=True,
    )

    prediction_id = Column(
        Integer,
        ForeignKey(
            "market_predictions.id"
        ),
        nullable=False,
        index=True,
    )

    market_code = Column(
        String,
        nullable=False,
        index=True,
    )

    selection = Column(
        String,
        nullable=False,
    )

    probability = Column(
        Float,
        nullable=False,
    )

    model_version = Column(
        String,
        nullable=False,
    )

    market_status = Column(
        String,
        nullable=False,
    )

    signal_eligible = Column(
        Boolean,
        nullable=False,
        default=False,
    )

    combination_eligible = Column(
        Boolean,
        nullable=False,
        default=False,
    )

    actual_result = Column(
        String,
        nullable=True,
    )

    correct = Column(
        Boolean,
        nullable=True,
    )

    created_at = Column(
        DateTime(
            timezone=True
        ),
        nullable=False,
        default=lambda:
            datetime.now(
                timezone.utc
            ),
    )

    evaluated_at = Column(
        DateTime(
            timezone=True
        ),
        nullable=True,
    )