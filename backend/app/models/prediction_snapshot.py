from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    Float,
    String,
    DateTime,
    ForeignKey,
)

from app.database.database import Base


class PredictionSnapshot(Base):
    __tablename__ = "prediction_snapshots"

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

    main_pick = Column(
        String,
        nullable=False,
    )

    confidence = Column(
        Float,
        nullable=False,
    )

    home_win = Column(
        Float,
        nullable=False,
    )

    draw = Column(
        Float,
        nullable=False,
    )

    away_win = Column(
        Float,
        nullable=False,
    )

    over_25 = Column(
        Float,
        nullable=True,
    )

    btts_yes = Column(
        Float,
        nullable=True,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True,
    )

    # ==========================================
    # OFFICIAL PREDICTION
    # ==========================================

    is_official = Column(
        Integer,
        default=0,
        nullable=False,
        index=True,
    )

    official_at = Column(
        DateTime,
        nullable=True,
    )

    # ==========================================
    # EVALUATION
    # ==========================================

    actual_result = Column(
        String,
        nullable=True,
    )

    result_correct = Column(
        Integer,
        nullable=True,
    )

    actual_over_25 = Column(
        Integer,
        nullable=True,
    )

    over_25_correct = Column(
        Integer,
        nullable=True,
    )

    actual_btts = Column(
        Integer,
        nullable=True,
    )

    btts_correct = Column(
        Integer,
        nullable=True,
    )