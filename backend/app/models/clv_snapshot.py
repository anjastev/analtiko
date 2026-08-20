from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
)

from app.database.database import Base


class CLVSnapshot(Base):
    __tablename__ = "clv_snapshots"

    id = Column(
        Integer,
        primary_key=True,
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

    bookmaker = Column(
        String,
        nullable=True,
    )

    recommended_odds = Column(
        Float,
        nullable=False,
    )

    closing_odds = Column(
        Float,
        nullable=True,
    )

    recommended_probability = Column(
        Float,
        nullable=True,
    )

    closing_probability = Column(
        Float,
        nullable=True,
    )

    clv_pct = Column(
        Float,
        nullable=True,
    )

    status = Column(
        String,
        nullable=False,
        default="WAITING",
        index=True,
    )

    recommendation_time = Column(
        DateTime,
        nullable=True,
    )

    closing_time = Column(
        DateTime,
        nullable=True,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )