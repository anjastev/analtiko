from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import relationship

from app.database.database import Base


class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)

    external_id = Column(
        Integer,
        unique=True,
        nullable=True,
        index=True,
    )

    league_id = Column(
        Integer,
        ForeignKey("leagues.id"),
        nullable=False,
    )

    home_team_id = Column(
        Integer,
        ForeignKey("teams.id"),
        nullable=False,
    )

    away_team_id = Column(
        Integer,
        ForeignKey("teams.id"),
        nullable=False,
    )

    match_date = Column(DateTime, nullable=False)

    status = Column(
        String,
        default="scheduled",
    )

    home_score = Column(Integer, nullable=True)
    away_score = Column(Integer, nullable=True)

    venue = Column(String, nullable=True)
    round = Column(String, nullable=True)

    league = relationship("League")

    home_team = relationship(
        "Team",
        foreign_keys=[home_team_id],
    )

    away_team = relationship(
        "Team",
        foreign_keys=[away_team_id],
    )