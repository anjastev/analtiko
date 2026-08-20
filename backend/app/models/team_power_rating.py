from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
)

from app.database.database import Base


class TeamPowerRating(Base):
    __tablename__ = "team_power_ratings"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    team_id = Column(
        Integer,
        ForeignKey("teams.id"),
        nullable=False,
        index=True,
    )

    match_id = Column(
        Integer,
        ForeignKey("matches.id"),
        nullable=False,
        index=True,
    )

    rating_before = Column(
        Float,
        nullable=False,
    )

    rating_after = Column(
        Float,
        nullable=False,
    )

    opponent_rating_before = Column(
        Float,
        nullable=False,
    )

    expected_score = Column(
        Float,
        nullable=False,
    )

    actual_score = Column(
        Float,
        nullable=False,
    )

    rating_change = Column(
        Float,
        nullable=False,
    )

    calculated_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )