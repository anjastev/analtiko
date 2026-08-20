from datetime import date, timedelta

from app.collectors.api_football import APIFootballClient
from app.database.database import (
    Base,
    SessionLocal,
    engine,
)
from app.models.match import Match
from app.services.history_sync import (
    sync_fixture_to_team_history,
)
from datetime import datetime, timezone
import app.models


# Колку наназад ќе бараме.
# За прв тест ставаме 120 дена.
DAYS_BACK = 120

# За да не трошиме quota,
# прво анализираме тимови само од првите 3 upcoming matches.
MATCHES_TO_PROCESS = 3
HISTORY_SEASON = 2024

def run():
    Base.metadata.create_all(
        bind=engine
    )

    client = APIFootballClient()
    db = SessionLocal()

    date_from = "2024-01-01"
    date_to = "2024-12-31"

    total_api_calls = 0
    total_fixtures = 0
    total_entries = 0

    try:
        now = datetime.now(
            timezone.utc
        )

        matches = (
            db.query(Match)
            .filter(
                Match.match_date >= now
            )
            .order_by(
                Match.match_date.asc()
            )
            .limit(
                MATCHES_TO_PROCESS
            )
            .all()
        )

        if not matches:
            print("No matches found.")
            return

        # --------------------------------------------
        # Collect unique teams
        # --------------------------------------------

        teams = {}

        for match in matches:
            teams[
                match.home_team.external_id
            ] = match.home_team

            teams[
                match.away_team.external_id
            ] = match.away_team

        teams = {
            external_id: team
            for external_id, team
            in teams.items()
            if external_id is not None
        }

        print()
        print("=" * 70)
        print("ANALITIKO TEAM HISTORY SYNC")
        print("=" * 70)

        print(
            f"Matches selected: {len(matches)}"
        )

        print(
            f"Unique teams: {len(teams)}"
        )

        print(
            f"Range: {date_from} -> {date_to}"
        )

        # --------------------------------------------
        # Fetch history per team
        # --------------------------------------------

        for external_id, team in teams.items():

            print()
            print("-" * 70)

            print(
                f"Fetching history for "
                f"{team.name}"
            )

            print(
                f"External team ID: "
                f"{external_id}"
            )

            try:
                data = (
                    client.get_team_fixtures_by_date_range(
                        team_id=external_id,
                        date_from=date_from,
                        date_to=date_to,
                        season=HISTORY_SEASON,
                    )
                )

                total_api_calls += 1

                errors = data.get(
                    "errors",
                    {}
                )

                if errors:
                    print(
                        f"API errors: {errors}"
                    )
                    continue

                fixtures = data.get(
                    "response",
                    [],
                )

                print(
                    f"Fixtures received: "
                    f"{len(fixtures)}"
                )

                total_fixtures += len(
                    fixtures
                )

                if not fixtures:
                    continue

                # Latest first
                fixtures.sort(
                    key=lambda item:
                        item["fixture"]["date"],
                    reverse=True,
                )

                # For form we only really need recent results.
                recent_fixtures = fixtures[:10]

                for fixture in recent_fixtures:

                    created = (
                        sync_fixture_to_team_history(
                            db=db,
                            fixture_data=fixture,
                        )
                    )

                    total_entries += (
                        created
                    )

                db.commit()

            except Exception as error:

                db.rollback()

                print(
                    f"FAILED: {error}"
                )

        print()
        print("=" * 70)
        print("HISTORY SYNC COMPLETE")
        print("=" * 70)

        print(
            f"API calls: {total_api_calls}"
        )

        print(
            f"Fixtures received: "
            f"{total_fixtures}"
        )

        print(
            f"History rows created: "
            f"{total_entries}"
        )

    finally:
        db.close()


if __name__ == "__main__":
    run()