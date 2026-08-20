from datetime import datetime

from pydantic import BaseModel


class TeamResponse(BaseModel):
    id: int
    name: str
    country: str | None = None
    logo: str | None = None

    class Config:
        from_attributes = True


class LeagueResponse(BaseModel):
    id: int
    name: str
    country: str
    logo: str | None = None

    class Config:
        from_attributes = True


class MatchResponse(BaseModel):
    id: int
    match_date: datetime
    status: str
    home_score: int | None = None
    away_score: int | None = None

    league: LeagueResponse
    home_team: TeamResponse
    away_team: TeamResponse

    class Config:
        from_attributes = True