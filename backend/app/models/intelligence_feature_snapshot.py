from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
)

from app.database.database import Base


class IntelligenceFeatureSnapshot(Base):
    __tablename__ = "intelligence_feature_snapshots"

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

    # ========================================================
    # POWER
    # ========================================================

    home_elo = Column(
        Float,
        nullable=False,
    )

    away_elo = Column(
        Float,
        nullable=False,
    )

    elo_difference = Column(
        Float,
        nullable=False,
    )

    # ========================================================
    # FORM
    # ========================================================

    home_weighted_form = Column(
        Float,
        nullable=False,
    )

    away_weighted_form = Column(
        Float,
        nullable=False,
    )

    home_opponent_strength = Column(
        Float,
        nullable=False,
    )

    away_opponent_strength = Column(
        Float,
        nullable=False,
    )

    home_strength_adjusted_form = Column(
        Float,
        nullable=False,
    )

    away_strength_adjusted_form = Column(
        Float,
        nullable=False,
    )

    # ========================================================
    # HISTORY COVERAGE
    # ========================================================

    home_history_count = Column(
        Integer,
        nullable=False,
    )

    away_history_count = Column(
        Integer,
        nullable=False,
    )

    # ========================================================
    # MARKET
    # ========================================================

    home_market_probability = Column(
        Float,
        nullable=True,
    )

    draw_market_probability = Column(
        Float,
        nullable=True,
    )

    away_market_probability = Column(
        Float,
        nullable=True,
    )

    home_market_dispersion = Column(
        Float,
        nullable=True,
    )

    draw_market_dispersion = Column(
        Float,
        nullable=True,
    )

    away_market_dispersion = Column(
        Float,
        nullable=True,
    )

    home_odds_movement = Column(
        Float,
        nullable=True,
    )

    draw_odds_movement = Column(
        Float,
        nullable=True,
    )

    away_odds_movement = Column(
        Float,
        nullable=True,
    )

    # ========================================================
    # SNAPSHOT
    # ========================================================

    snapshot_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True,
    )