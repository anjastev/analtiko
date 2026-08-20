from pydantic import BaseModel


class MatchStatsResponse(BaseModel):
    match_id: int

    home_form: float
    away_form: float

    home_goals_avg: float
    away_goals_avg: float

    home_shots_avg: float
    away_shots_avg: float

    home_corners_avg: float
    away_corners_avg: float

    home_possession_avg: float
    away_possession_avg: float

    home_xg_avg: float
    away_xg_avg: float

    class Config:
        from_attributes = True