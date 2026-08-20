from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
)

from app.database.database import Base


class H2HMatch(Base):
    __tablename__ = "h2h_matches"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    fixture_external_id = Column(
        Integer,
        unique=True,
        nullable=False,
        index=True,
    )

    home_team_external_id = Column(
        Integer,
        nullable=False,
        index=True,
    )

    away_team_external_id = Column(
        Integer,
        nullable=False,
        index=True,
    )

    home_team_name = Column(
        String,
        nullable=False,
    )

    away_team_name = Column(
        String,
        nullable=False,
    )

    home_goals = Column(
        Integer,
        nullable=False,
    )

    away_goals = Column(
        Integer,
        nullable=False,
    )

    match_date = Column(
        DateTime,
        nullable=False,
        index=True,
    )