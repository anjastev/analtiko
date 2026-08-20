from datetime import datetime

from sqlalchemy.orm import Session

from app.collectors.api_football import APIFootballClient
from app.models.h2h import H2HMatch


def save_h2h_matches(
    db: Session,
    fixtures: list[dict],
) -> int:

    created = 0

    for item in fixtures:
        fixture = item.get("fixture", {})
        teams = item.get("teams", {})
        goals = item.get("goals", {})

        fixture_id = fixture.get("id")

        if not fixture_id:
            continue

        home = teams.get("home", {})
        away = teams.get("away", {})

        home_goals = goals.get("home")
        away_goals = goals.get("away")

        if (
            home_goals is None
            or away_goals is None
        ):
            continue

        existing = (
            db.query(H2HMatch)
            .filter(
                H2HMatch.fixture_external_id
                == fixture_id
            )
            .first()
        )

        if existing:
            continue

        match_date = datetime.fromisoformat(
            fixture["date"].replace(
                "Z",
                "+00:00",
            )
        )

        row = H2HMatch(
            fixture_external_id=fixture_id,

            home_team_external_id=
                home["id"],

            away_team_external_id=
                away["id"],

            home_team_name=
                home["name"],

            away_team_name=
                away["name"],

            home_goals=
                home_goals,

            away_goals=
                away_goals,

            match_date=
                match_date,
        )

        db.add(row)

        created += 1

    db.commit()

    return created


def get_cached_h2h(
    db: Session,
    team_a_id: int,
    team_b_id: int,
    limit: int = 5,
) -> list[H2HMatch]:

    return (
        db.query(H2HMatch)
        .filter(
            (
                (
                    H2HMatch.home_team_external_id
                    == team_a_id
                )
                &
                (
                    H2HMatch.away_team_external_id
                    == team_b_id
                )
            )
            |
            (
                (
                    H2HMatch.home_team_external_id
                    == team_b_id
                )
                &
                (
                    H2HMatch.away_team_external_id
                    == team_a_id
                )
            )
        )
        .order_by(
            H2HMatch.match_date.desc()
        )
        .limit(limit)
        .all()
    )


def get_or_fetch_h2h(
    db: Session,
    client: APIFootballClient,
    team_a_id: int,
    team_b_id: int,
    limit: int = 5,
):

    cached = get_cached_h2h(
        db=db,
        team_a_id=team_a_id,
        team_b_id=team_b_id,
        limit=limit,
    )

    if len(cached) >= limit:
        return cached

    data = client.get_head_to_head(
        home_team_id=team_a_id,
        away_team_id=team_b_id,
        last=limit,
    )

    fixtures = data.get(
        "response",
        [],
    )

    if fixtures:
        save_h2h_matches(
            db=db,
            fixtures=fixtures,
        )

    return get_cached_h2h(
        db=db,
        team_a_id=team_a_id,
        team_b_id=team_b_id,
        limit=limit,
    )