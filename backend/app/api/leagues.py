from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db

from app.models.league import League
from app.models.match import Match


router = APIRouter(
    prefix="/api/leagues",
    tags=["Leagues"],
)


@router.get("")
def get_leagues(
    db: Session = Depends(get_db),
):
    leagues = (
        db.query(League)
        .order_by(League.name.asc())
        .all()
    )

    results = []

    for league in leagues:
        matches_count = (
            db.query(Match)
            .filter(
                Match.league_id == league.id
            )
            .count()
        )

        results.append(
            {
                "id": league.id,
                "external_id": league.external_id,
                "name": league.name,
                "country": league.country,
                "logo": league.logo,
                "matches_count": matches_count,
            }
        )

    return results


@router.get("/{league_id}")
def get_league_details(
    league_id: int,
    db: Session = Depends(get_db),
):
    league = (
        db.query(League)
        .filter(
            League.id == league_id
        )
        .first()
    )

    if not league:
        raise HTTPException(
            status_code=404,
            detail="League not found",
        )

    matches = (
        db.query(Match)
        .filter(
            Match.league_id == league.id
        )
        .order_by(
            Match.match_date.asc()
        )
        .all()
    )

    return {
        "id": league.id,
        "external_id": league.external_id,
        "name": league.name,
        "country": league.country,
        "logo": league.logo,
        "matches_count": len(matches),

        "matches": [
            {
                "id": match.id,
                "home_team": {
                    "id": match.home_team.id,
                    "name": match.home_team.name,
                    "logo": match.home_team.logo,
                },
                "away_team": {
                    "id": match.away_team.id,
                    "name": match.away_team.name,
                    "logo": match.away_team.logo,
                },
                "match_date": match.match_date,
                "status": match.status,
                "home_score": match.home_score,
                "away_score": match.away_score,
            }
            for match in matches
        ],
    }