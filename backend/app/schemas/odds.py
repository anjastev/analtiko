from datetime import datetime

from pydantic import BaseModel


class OddsResponse(BaseModel):
    id: int
    match_id: int

    bookmaker: str | None = None

    home_win: float | None = None
    draw: float | None = None
    away_win: float | None = None

    over_25: float | None = None
    under_25: float | None = None

    btts_yes: float | None = None
    btts_no: float | None = None

    recorded_at: datetime

    class Config:
        from_attributes = True