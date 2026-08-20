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


class Odds(Base):
    __tablename__ = "odds"

    id = Column(Integer, primary_key=True, index=True)

    match_id = Column(
        Integer,
        ForeignKey("matches.id"),
        nullable=False,
        index=True,
    )

    bookmaker = Column(
        String,
        nullable=True,
    )

    home_win = Column(Float, nullable=True)
    draw = Column(Float, nullable=True)
    away_win = Column(Float, nullable=True)

    over_25 = Column(Float, nullable=True)
    under_25 = Column(Float, nullable=True)

    btts_yes = Column(Float, nullable=True)
    btts_no = Column(Float, nullable=True)

    recorded_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True,
    )