from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
)

from sqlalchemy.sql import func

from app.database.database import Base


class MarketPrediction(Base):
    __tablename__ = "market_predictions"

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

    model_version = Column(
        String,
        nullable=False,
    )

    selection = Column(
        String,
        nullable=False,
    )

    probability = Column(
        Float,
        nullable=False,
    )

    confidence = Column(
        Float,
        nullable=True,
    )

    confidence_level = Column(
        String,
        nullable=True,
    )

    is_recommended = Column(
        Boolean,
        default=False,
        nullable=False,
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
        DateTime,
        server_default=func.now(),
        nullable=False,
    )

    evaluated_at = Column(
        DateTime,
        nullable=True,
    )