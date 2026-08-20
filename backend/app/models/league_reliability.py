from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
)

from app.database.database import Base


class LeagueReliability(Base):
    __tablename__ = "league_reliability"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    league_id = Column(
        Integer,
        ForeignKey("leagues.id"),
        nullable=False,
        unique=True,
        index=True,
    )

    evaluated_signals = Column(
        Integer,
        nullable=False,
        default=0,
    )

    wins = Column(
        Integer,
        nullable=False,
        default=0,
    )

    losses = Column(
        Integer,
        nullable=False,
        default=0,
    )

    hit_rate = Column(
        Float,
        nullable=True,
    )

    average_edge = Column(
        Float,
        nullable=True,
    )

    roi = Column(
        Float,
        nullable=True,
    )

    reliability_score = Column(
        Float,
        nullable=False,
        default=0.70,
    )

    sample_confidence = Column(
        Float,
        nullable=False,
        default=0.0,
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )