from datetime import datetime

from sqlalchemy.orm import Session

from app.models.team import Team
from app.models.team_match_history import TeamMatchHistory


FINISHED_STATUSES = {
    "FT",
    "AET",
    "PEN",
}


def determine_result(
    goals_for: int,
    goals_against: int,
) -> str:

    if goals_for > goals_against:
        return "W"

    if goals_for < goals_against:
        return "L"

    return "D"


def create_history_entry(
    db: Session,
    team: Team,
    fixture_external_id: int,
    match_date: datetime,
    league_name: str | None,
    opponent_name: str,
    venue: str,
    goals_for: int,
    goals_against: int,
) -> int:

    existing = (
        db.query(TeamMatchHistory)
        .filter(
            TeamMatchHistory.team_id
            == team.id,

            TeamMatchHistory.fixture_external_id
            == fixture_external_id,
        )
        .first()
    )

    if existing:
        return 0

    entry = TeamMatchHistory(
        team_id=team.id,

        fixture_external_id=
            fixture_external_id,

        match_date=match_date,

        league_name=league_name,

        opponent_name=
            opponent_name,

        venue=venue,

        goals_for=
            goals_for,

        goals_against=
            goals_against,

        result=determine_result(
            goals_for,
            goals_against,
        ),
    )

    db.add(entry)

    return 1


def sync_fixture_to_team_history(
    db: Session,
    fixture_data: dict,
) -> int:

    fixture = (
        fixture_data.get(
            "fixture",
            {}
        )
    )

    status = (
        fixture
        .get("status", {})
        .get("short")
    )

    if status not in FINISHED_STATUSES:
        return 0

    teams_data = fixture_data.get(
        "teams",
        {}
    )

    home = teams_data.get(
        "home",
        {}
    )

    away = teams_data.get(
        "away",
        {}
    )

    goals = fixture_data.get(
        "goals",
        {}
    )

    home_goals = goals.get(
        "home"
    )

    away_goals = goals.get(
        "away"
    )

    if (
        home_goals is None
        or away_goals is None
    ):
        return 0

    fixture_external_id = (
        fixture.get("id")
    )

    fixture_date = (
        fixture.get("date")
    )

    if (
        not fixture_external_id
        or not fixture_date
    ):
        return 0

    match_date = datetime.fromisoformat(
        fixture_date.replace(
            "Z",
            "+00:00",
        )
    )

    league_name = (
        fixture_data
        .get("league", {})
        .get("name")
    )

    home_team = (
        db.query(Team)
        .filter(
            Team.external_id
            == home.get("id")
        )
        .first()
    )

    away_team = (
        db.query(Team)
        .filter(
            Team.external_id
            == away.get("id")
        )
        .first()
    )

    created = 0

    # Home team exists locally
    if home_team:

        created += create_history_entry(
            db=db,

            team=home_team,

            fixture_external_id=
                fixture_external_id,

            match_date=
                match_date,

            league_name=
                league_name,

            opponent_name=
                away.get(
                    "name",
                    "Unknown",
                ),

            venue="home",

            goals_for=
                home_goals,

            goals_against=
                away_goals,
        )

    # Away team exists locally
    if away_team:

        created += create_history_entry(
            db=db,

            team=away_team,

            fixture_external_id=
                fixture_external_id,

            match_date=
                match_date,

            league_name=
                league_name,

            opponent_name=
                home.get(
                    "name",
                    "Unknown",
                ),

            venue="away",

            goals_for=
                away_goals,

            goals_against=
                home_goals,
        )

    return created