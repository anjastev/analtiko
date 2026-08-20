from datetime import datetime

from app.collectors.api_football import APIFootballClient
from app.database.database import SessionLocal

from app.models.league import League
from app.models.team import Team
from app.models.match import Match


# ============================================================
# CONFIG
# ============================================================

LEAGUE_ID = 140
LEAGUE_NAME = "La Liga"

SEASON = 2024

# За прв тест не внесуваме цела сезона.
# Кога ќе видиме дека работи, стави None.
MAX_MATCHES = None


FINISHED_STATUSES = {
    "FT",
    "AET",
    "PEN",
}


# ============================================================
# HELPERS
# ============================================================

def parse_date(
    value: str,
) -> datetime:

    return datetime.fromisoformat(
        value.replace(
            "Z",
            "+00:00",
        )
    )


def get_or_create_league(
    db,
    league_data: dict,
) -> League:

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
        external_id=
            external_id,

        name=
            league_data.get(
                "name",
                LEAGUE_NAME,
            ),

        country=
            league_data.get(
                "country",
                "Spain",
            ),

        logo=
            league_data.get(
                "logo"
            ),
    )

    db.add(league)
    db.flush()

    return league


def get_or_create_team(
    db,
    team_data: dict,
) -> Team:

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
        # Update useful metadata if missing
        if (
            not team.logo
            and team_data.get("logo")
        ):
            team.logo = (
                team_data.get("logo")
            )

        return team

    team = Team(
        external_id=
            external_id,

        name=
            team_data.get(
                "name",
                "Unknown",
            ),

        country="Spain",

        logo=
            team_data.get(
                "logo"
            ),
    )

    db.add(team)
    db.flush()

    return team


# ============================================================
# MAIN
# ============================================================

def run():
    db = SessionLocal()

    client = APIFootballClient()

    created_matches = 0
    updated_matches = 0
    skipped_matches = 0
    failed_matches = 0

    try:

        print()
        print("=" * 70)
        print("ANALITIKO HISTORICAL BACKFILL")
        print("=" * 70)

        print(
            f"League: {LEAGUE_NAME}"
        )

        print(
            f"League ID: {LEAGUE_ID}"
        )

        print(
            f"Season: {SEASON}"
        )

        print()
        print(
            "Fetching fixtures..."
        )


        data = (
            client.get_league_fixtures(
                league_id=
                    LEAGUE_ID,

                season=
                    SEASON,
            )
        )


        errors = data.get(
            "errors",
            {}
        )

        if errors:
            print()
            print(
                f"API errors: {errors}"
            )

            return


        fixtures = data.get(
            "response",
            []
        )


        print(
            f"API returned: "
            f"{len(fixtures)} fixtures"
        )


        # ====================================================
        # KEEP FINISHED ONLY
        # ====================================================

        finished_fixtures = []

        for item in fixtures:

            status = (
                item
                .get("fixture", {})
                .get("status", {})
                .get("short")
            )

            if (
                status
                in FINISHED_STATUSES
            ):
                finished_fixtures.append(
                    item
                )


        finished_fixtures.sort(
            key=lambda item:
                item["fixture"]["date"]
        )


        print(
            f"Finished fixtures: "
            f"{len(finished_fixtures)}"
        )


        if MAX_MATCHES is not None:

            finished_fixtures = (
                finished_fixtures[
                    :MAX_MATCHES
                ]
            )

            print(
                f"Processing first "
                f"{len(finished_fixtures)} "
                f"fixtures"
            )


        # ====================================================
        # SAVE
        # ====================================================

        for fixture_data in (
            finished_fixtures
        ):

            fixture = (
                fixture_data.get(
                    "fixture",
                    {}
                )
            )

            fixture_id = fixture.get(
                "id"
            )

            try:

                league_data = (
                    fixture_data.get(
                        "league",
                        {}
                    )
                )

                teams_data = (
                    fixture_data.get(
                        "teams",
                        {}
                    )
                )

                goals = (
                    fixture_data.get(
                        "goals",
                        {}
                    )
                )


                home_data = (
                    teams_data.get(
                        "home",
                        {}
                    )
                )

                away_data = (
                    teams_data.get(
                        "away",
                        {}
                    )
                )


                home_score = (
                    goals.get(
                        "home"
                    )
                )

                away_score = (
                    goals.get(
                        "away"
                    )
                )


                if (
                    fixture_id is None
                    or home_data.get("id")
                    is None
                    or away_data.get("id")
                    is None
                    or home_score is None
                    or away_score is None
                ):

                    skipped_matches += 1

                    print(
                        "Skipped incomplete fixture"
                    )

                    continue


                league = (
                    get_or_create_league(
                        db,
                        league_data,
                    )
                )


                home_team = (
                    get_or_create_team(
                        db,
                        home_data,
                    )
                )


                away_team = (
                    get_or_create_team(
                        db,
                        away_data,
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
                        updated_matches += 1

                    else:
                        skipped_matches += 1


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

                created_matches += 1


                print(
                    f"Added: "
                    f"{home_team.name} "
                    f"{home_score}-"
                    f"{away_score} "
                    f"{away_team.name}"
                )


            except Exception as error:

                failed_matches += 1

                print(
                    f"FAILED fixture "
                    f"{fixture_id}: "
                    f"{error}"
                )


        db.commit()


        print()
        print("=" * 70)
        print("BACKFILL COMPLETE")
        print("=" * 70)

        print(
            f"Created: {created_matches}"
        )

        print(
            f"Updated: {updated_matches}"
        )

        print(
            f"Skipped: {skipped_matches}"
        )

        print(
            f"Failed: {failed_matches}"
        )


    except Exception:

        db.rollback()

        raise


    finally:
        db.close()


if __name__ == "__main__":
    run()