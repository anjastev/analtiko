from datetime import datetime

from app.collectors.api_football import APIFootballClient
from app.database.database import SessionLocal

from app.models.league import League
from app.models.team import Team
from app.models.match import Match


LEAGUES = [
    {
        "id": 140,
        "name": "La Liga",
        "country": "Spain",
        "season": 2024,
    },
    {
        "id": 39,
        "name": "Premier League",
        "country": "England",
        "season": 2024,
    },
    {
        "id": 135,
        "name": "Serie A",
        "country": "Italy",
        "season": 2024,
    },
    {
        "id": 78,
        "name": "Bundesliga",
        "country": "Germany",
        "season": 2024,
    },
]


FINISHED_STATUSES = {
    "FT",
    "AET",
    "PEN",
}


def parse_date(value: str) -> datetime:
    return datetime.fromisoformat(
        value.replace(
            "Z",
            "+00:00",
        )
    )


def get_or_create_league(
    db,
    league_data,
    fallback,
):
    external_id = league_data.get(
        "id"
    )

    league = (
        db.query(League)
        .filter(
            League.external_id
            == external_id
        )
        .first()
    )

    if league:
        return league

    league = League(
        external_id=external_id,

        name=league_data.get(
            "name",
            fallback["name"],
        ),

        country=league_data.get(
            "country",
            fallback["country"],
        ),

        logo=league_data.get(
            "logo"
        ),
    )

    db.add(league)
    db.flush()

    return league


def get_or_create_team(
    db,
    team_data,
    country,
):
    external_id = team_data.get(
        "id"
    )

    team = (
        db.query(Team)
        .filter(
            Team.external_id
            == external_id
        )
        .first()
    )

    if team:
        if (
            not team.logo
            and team_data.get("logo")
        ):
            team.logo = (
                team_data.get("logo")
            )

        return team

    team = Team(
        external_id=external_id,

        name=team_data.get(
            "name",
            "Unknown",
        ),

        country=country,

        logo=team_data.get(
            "logo"
        ),
    )

    db.add(team)
    db.flush()

    return team


def process_league(
    db,
    client,
    config,
):
    created = 0
    updated = 0
    skipped = 0
    failed = 0

    print()
    print("=" * 70)
    print(
        f"{config['name']} "
        f"{config['season']}"
    )
    print("=" * 70)

    data = (
        client.get_league_fixtures(
            league_id=config["id"],
            season=config["season"],
        )
    )

    errors = data.get(
        "errors",
        {}
    )

    if errors:
        print(
            f"API errors: {errors}"
        )

        return {
            "created": 0,
            "updated": 0,
            "skipped": 0,
            "failed": 1,
        }

    fixtures = data.get(
        "response",
        []
    )

    finished = []

    for item in fixtures:
        status = (
            item
            .get("fixture", {})
            .get("status", {})
            .get("short")
        )

        if status in FINISHED_STATUSES:
            finished.append(
                item
            )

    finished.sort(
        key=lambda item:
            item["fixture"]["date"]
    )

    print(
        f"API fixtures: "
        f"{len(fixtures)}"
    )

    print(
        f"Finished: "
        f"{len(finished)}"
    )

    for item in finished:

        fixture = item.get(
            "fixture",
            {}
        )

        fixture_id = fixture.get(
            "id"
        )

        try:
            league_data = item.get(
                "league",
                {}
            )

            teams_data = item.get(
                "teams",
                {}
            )

            goals = item.get(
                "goals",
                {}
            )

            home_data = teams_data.get(
                "home",
                {}
            )

            away_data = teams_data.get(
                "away",
                {}
            )

            home_score = goals.get(
                "home"
            )

            away_score = goals.get(
                "away"
            )

            if (
                fixture_id is None
                or home_data.get("id") is None
                or away_data.get("id") is None
                or home_score is None
                or away_score is None
            ):
                skipped += 1
                continue

            league = (
                get_or_create_league(
                    db,
                    league_data,
                    config,
                )
            )

            home_team = (
                get_or_create_team(
                    db,
                    home_data,
                    config["country"],
                )
            )

            away_team = (
                get_or_create_team(
                    db,
                    away_data,
                    config["country"],
                )
            )

            existing = (
                db.query(Match)
                .filter(
                    Match.external_id
                    == fixture_id
                )
                .first()
            )

            match_date = (
                parse_date(
                    fixture.get(
                        "date"
                    )
                )
            )

            status = (
                fixture
                .get("status", {})
                .get("short")
            )

            if existing:
                changed = False

                if (
                    existing.status
                    != status
                ):
                    existing.status = (
                        status
                    )
                    changed = True

                if (
                    existing.home_score
                    != home_score
                ):
                    existing.home_score = (
                        home_score
                    )
                    changed = True

                if (
                    existing.away_score
                    != away_score
                ):
                    existing.away_score = (
                        away_score
                    )
                    changed = True

                if changed:
                    updated += 1
                else:
                    skipped += 1

                continue

            match = Match(
                external_id=
                    fixture_id,

                league_id=
                    league.id,

                home_team_id=
                    home_team.id,

                away_team_id=
                    away_team.id,

                match_date=
                    match_date,

                status=
                    status,

                home_score=
                    home_score,

                away_score=
                    away_score,
            )

            db.add(match)

            created += 1

        except Exception as error:
            db.rollback()

            failed += 1

            print(
                f"FAILED fixture "
                f"{fixture_id}: "
                f"{error}"
            )

            continue

    db.commit()

    print()
    print(
        f"Created: {created}"
    )

    print(
        f"Updated: {updated}"
    )

    print(
        f"Skipped: {skipped}"
    )

    print(
        f"Failed: {failed}"
    )

    return {
        "created": created,
        "updated": updated,
        "skipped": skipped,
        "failed": failed,
    }


def run():
    db = SessionLocal()

    client = APIFootballClient()

    totals = {
        "created": 0,
        "updated": 0,
        "skipped": 0,
        "failed": 0,
    }

    try:

        print()
        print("=" * 70)
        print(
            "ANALITIKO MULTI-LEAGUE BACKFILL"
        )
        print("=" * 70)

        for config in LEAGUES:

            result = (
                process_league(
                    db=db,
                    client=client,
                    config=config,
                )
            )

            for key in totals:
                totals[key] += (
                    result[key]
                )

        print()
        print("=" * 70)
        print(
            "MULTI-LEAGUE BACKFILL COMPLETE"
        )
        print("=" * 70)

        print(
            f"Created: "
            f"{totals['created']}"
        )

        print(
            f"Updated: "
            f"{totals['updated']}"
        )

        print(
            f"Skipped: "
            f"{totals['skipped']}"
        )

        print(
            f"Failed: "
            f"{totals['failed']}"
        )

    finally:
        db.close()


if __name__ == "__main__":
    run()