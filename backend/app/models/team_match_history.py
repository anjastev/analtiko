from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
)

from app.database.database import Base


class TeamMatchHistory(Base):
    __tablename__ = "team_match_history"

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

    fixture_external_id = Column(
        Integer,
        nullable=False,
        index=True,
    )

    match_date = Column(
        DateTime,
        nullable=False,
        index=True,
    )

    league_name = Column(
        String,
        nullable=True,
    )

    opponent_name = Column(
        String,
        nullable=False,
    )

    venue = Column(
        String,
        nullable=False,
    )

    goals_for = Column(
        Integer,
        nullable=False,
    )

    goals_against = Column(
        Integer,
        nullable=False,
    )

    result = Column(
        String,
        nullable=False,
    )