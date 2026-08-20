from datetime import datetime

from sqlalchemy.orm import Session

from app.models.league import League
from app.models.team import Team
from app.models.match import Match


def get_or_create_league(
    db: Session,
    league_data: dict,
) -> League:

    external_id = league_data["id"]

    league = (
        db.query(League)
        .filter(League.external_id == external_id)
        .first()
    )

    if league:
        league.name = league_data["name"]
        league.country = league_data.get("country") or "Unknown"
        league.logo = league_data.get("logo")

        return league

    league = League(
        external_id=external_id,
        name=league_data["name"],
        country=league_data.get("country") or "Unknown",
        logo=league_data.get("logo"),
    )

    db.add(league)
    db.flush()

    return league


def get_or_create_team(
    db: Session,
    team_data: dict,
    country: str | None = None,
) -> Team:

    external_id = team_data["id"]

    team = (
        db.query(Team)
        .filter(Team.external_id == external_id)
        .first()
    )

    if team:
        team.name = team_data["name"]
        team.logo = team_data.get("logo")

        if country:
            team.country = country

        return team

    team = Team(
        external_id=external_id,
        name=team_data["name"],
        country=country,
        logo=team_data.get("logo"),
    )

    db.add(team)
    db.flush()

    return team


def sync_fixture(
    db: Session,
    fixture_data: dict,
) -> Match:

    fixture = fixture_data["fixture"]
    league_data = fixture_data["league"]

    home_data = fixture_data["teams"]["home"]
    away_data = fixture_data["teams"]["away"]

    goals = fixture_data.get("goals", {})

    league = get_or_create_league(
        db,
        league_data,
    )

    home_team = get_or_create_team(
        db,
        home_data,
        country=league_data.get("country"),
    )

    away_team = get_or_create_team(
        db,
        away_data,
        country=league_data.get("country"),
    )

    match = (
        db.query(Match)
        .filter(
            Match.external_id == fixture["id"]
        )
        .first()
    )

    match_date = datetime.fromisoformat(
        fixture["date"].replace("Z", "+00:00")
    )

    venue_data = fixture.get("venue") or {}
    venue_name = venue_data.get("name")

    status_data = fixture.get("status") or {}
    status = status_data.get("short", "NS")

    if match:
        match.league_id = league.id
        match.home_team_id = home_team.id
        match.away_team_id = away_team.id

        match.match_date = match_date
        match.status = status

        match.home_score = goals.get("home")
        match.away_score = goals.get("away")

        match.venue = venue_name
        match.round = league_data.get("round")

        return match

    match = Match(
        external_id=fixture["id"],

        league_id=league.id,
        home_team_id=home_team.id,
        away_team_id=away_team.id,

        match_date=match_date,
        status=status,

        home_score=goals.get("home"),
        away_score=goals.get("away"),

        venue=venue_name,
        round=league_data.get("round"),
    )

    db.add(match)
    db.flush()

    return match


def sync_fixtures(
    db: Session,
    fixtures: list[dict],
) -> int:

    count = 0

    for fixture in fixtures:
        sync_fixture(
            db=db,
            fixture_data=fixture,
        )

        count += 1

    db.commit()

    return count