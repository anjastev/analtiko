from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db

from app.models.team import Team
from app.models.match import Match
from app.models.team_match_history import TeamMatchHistory

from app.analytics.team_form import calculate_form_from_history


router = APIRouter(
    prefix="/api/teams",
    tags=["Teams"],
)


# ============================================================
# ALL TEAMS
# ============================================================

@router.get("")
def get_teams(
    db: Session = Depends(get_db),
):
    teams = (
        db.query(Team)
        .order_by(Team.name.asc())
        .all()
    )

    results = []

    for team in teams:
        history = (
            db.query(TeamMatchHistory)
            .filter(
                TeamMatchHistory.team_id == team.id
            )
            .order_by(
                TeamMatchHistory.match_date.desc()
            )
            .limit(5)
            .all()
        )

        form = calculate_form_from_history(
            history
        )

        results.append(
            {
                "id": team.id,
                "external_id": team.external_id,
                "name": team.name,
                "country": team.country,
                "logo": team.logo,
                "form": form,
            }
        )

    return results


# ============================================================
# TEAM DETAILS
# ============================================================

@router.get("/{team_id}")
def get_team_details(
    team_id: int,
    db: Session = Depends(get_db),
):
    team = (
        db.query(Team)
        .filter(
            Team.id == team_id
        )
        .first()
    )

    if not team:
        raise HTTPException(
            status_code=404,
            detail="Team not found",
        )

    history = (
        db.query(TeamMatchHistory)
        .filter(
            TeamMatchHistory.team_id == team.id
        )
        .order_by(
            TeamMatchHistory.match_date.desc()
        )
        .limit(10)
        .all()
    )

    form = calculate_form_from_history(
        history[:5]
    )

    upcoming_matches = (
        db.query(Match)
        .filter(
            (Match.home_team_id == team.id)
            |
            (Match.away_team_id == team.id)
        )
        .order_by(
            Match.match_date.asc()
        )
        .limit(10)
        .all()
    )

    return {
        "id": team.id,
        "external_id": team.external_id,
        "name": team.name,
        "country": team.country,
        "logo": team.logo,

        "form": form,

        "history": [
            {
                "fixture_external_id": item.fixture_external_id,
                "match_date": item.match_date,
                "league_name": item.league_name,
                "opponent_name": item.opponent_name,
                "venue": item.venue,
                "goals_for": item.goals_for,
                "goals_against": item.goals_against,
                "result": item.result,
            }
            for item in history
        ],

        "upcoming_matches": [
            {
                "id": match.id,
                "league": match.league.name,
                "home_team": match.home_team.name,
                "away_team": match.away_team.name,
                "match_date": match.match_date,
                "status": match.status,
            }
            for match in upcoming_matches
        ],
    }