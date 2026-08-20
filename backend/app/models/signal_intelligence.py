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


class SignalIntelligence(Base):
    __tablename__ = "signal_intelligence"

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

    raw_probability = Column(
        Float,
        nullable=False,
    )

    calibrated_probability = Column(
        Float,
        nullable=False,
    )

    calibration_status = Column(
        String,
        nullable=False,
        default="PROVISIONAL",
    )

    uncertainty = Column(
        Float,
        nullable=False,
    )

    data_quality_score = Column(
        Float,
        nullable=False,
    )

    market_agreement_score = Column(
        Float,
        nullable=False,
    )

    league_reliability = Column(
        Float,
        nullable=False,
    )

    elo_confidence = Column(
        Float,
        nullable=False,
    )

    quality_score = Column(
        Float,
        nullable=False,
        index=True,
    )

    quality_tier = Column(
        String,
        nullable=False,
        index=True,
    )

    production_eligible = Column(
        Integer,
        nullable=False,
        default=0,
        index=True,
    )
    anomaly_score = Column(
        Float,
        nullable=False,
        default=0.0,
    )

    anomaly_level = Column(
        String,
        nullable=False,
        default="NORMAL",
    )

    requires_review = Column(
        Integer,
        nullable=False,
        default=0,
    )

    calculated_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True,
    )