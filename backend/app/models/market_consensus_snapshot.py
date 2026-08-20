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


class MarketConsensusSnapshot(Base):
    __tablename__ = "market_consensus_snapshots"

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

    selection = Column(
        String,
        nullable=False,
        index=True,
    )

    bookmaker_count = Column(
        Integer,
        nullable=False,
    )

    best_odds = Column(
        Float,
        nullable=False,
    )

    median_odds = Column(
        Float,
        nullable=False,
    )

    mean_odds = Column(
        Float,
        nullable=False,
    )

    min_odds = Column(
        Float,
        nullable=False,
    )

    max_odds = Column(
        Float,
        nullable=False,
    )

    raw_implied_probability = Column(
        Float,
        nullable=False,
    )

    consensus_probability = Column(
        Float,
        nullable=True,
    )

    odds_dispersion = Column(
        Float,
        nullable=False,
    )

    opening_odds = Column(
        Float,
        nullable=True,
    )

    current_odds = Column(
        Float,
        nullable=False,
    )

    odds_change_pct = Column(
        Float,
        nullable=True,
    )

    snapshot_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True,
    )