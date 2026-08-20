from sqlalchemy import Column, Integer, Float, ForeignKey

from app.database.database import Base


class MatchStats(Base):
    __tablename__ = "match_stats"

    id = Column(Integer, primary_key=True, index=True)

    match_id = Column(
        Integer,
        ForeignKey("matches.id"),
        nullable=False,
        unique=True,
    )

    home_form = Column(Float, default=0)
    away_form = Column(Float, default=0)

    home_goals_avg = Column(Float, default=0)
    away_goals_avg = Column(Float, default=0)

    home_shots_avg = Column(Float, default=0)
    away_shots_avg = Column(Float, default=0)

    home_corners_avg = Column(Float, default=0)
    away_corners_avg = Column(Float, default=0)

    home_possession_avg = Column(Float, default=0)
    away_possession_avg = Column(Float, default=0)

    home_xg_avg = Column(Float, default=0)
    away_xg_avg = Column(Float, default=0)