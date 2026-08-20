from datetime import date, timedelta

from app.collectors.api_football import APIFootballClient
from app.config import SELECTED_LEAGUES
from app.database.database import Base, SessionLocal, engine
from app.services.fixture_sync import sync_fixtures

import app.models


def run():
    Base.metadata.create_all(bind=engine)

    client = APIFootballClient()

    start_date = date.today()
    days_to_sync = 3

    selected_ids = set(SELECTED_LEAGUES.keys())

    db = SessionLocal()

    total_received = 0
    total_selected = 0
    total_synced = 0

    try:
        for day_offset in range(days_to_sync):

            target_date = start_date + timedelta(
                days=day_offset
            )

            date_string = target_date.isoformat()

            print()
            print("=" * 60)
            print(f"Fetching fixtures for {date_string}")
            print("=" * 60)

            data = client.get_fixtures_by_date(
                date_string
            )

            fixtures = data.get("response", [])

            total_received += len(fixtures)

            print(
                f"API returned {len(fixtures)} fixtures"
            )

            selected_fixtures = [
                fixture
                for fixture in fixtures
                if fixture["league"]["id"]
                in selected_ids
            ]

            total_selected += len(
                selected_fixtures
            )

            print(
                f"Selected {len(selected_fixtures)} fixtures"
            )

            for fixture in selected_fixtures:
                league = fixture["league"]["name"]

                home = fixture["teams"]["home"]["name"]
                away = fixture["teams"]["away"]["name"]

                print(
                    f"  {league}: "
                    f"{home} vs {away}"
                )

            if selected_fixtures:

                synced = sync_fixtures(
                    db=db,
                    fixtures=selected_fixtures,
                )

                total_synced += synced

        print()
        print("=" * 60)
        print("SYNC COMPLETE")
        print("=" * 60)

        print(
            f"Received: {total_received}"
        )

        print(
            f"Selected: {total_selected}"
        )

        print(
            f"Synced: {total_synced}"
        )

    except Exception:

        db.rollback()
        raise

    finally:

        db.close()


if __name__ == "__main__":
    run()