from sqlalchemy import Column, Integer, String

from app.database.database import Base


class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)

    external_id = Column(
        Integer,
        unique=True,
        nullable=True,
        index=True,
    )

    name = Column(String, nullable=False)
    country = Column(String, nullable=True)
    logo = Column(String, nullable=True)