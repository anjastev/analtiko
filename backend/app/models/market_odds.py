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


class MarketOdds(Base):
    __tablename__ = "market_odds"

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

    bookmaker = Column(
        String,
        nullable=True,
        index=True,
    )

    odds = Column(
        Float,
        nullable=False,
    )

    source = Column(
        String,
        nullable=True,
    )

    recorded_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True,
    )