from sqlalchemy import Column, Integer, String

from app.database.database import Base


class League(Base):
    __tablename__ = "leagues"

    id = Column(Integer, primary_key=True, index=True)

    external_id = Column(
        Integer,
        unique=True,
        nullable=True,
        index=True,
    )

    name = Column(String, nullable=False)
    country = Column(String, nullable=False)
    logo = Column(String, nullable=True)