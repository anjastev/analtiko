from datetime import date

from app.collectors.api_football import APIFootballClient
from app.database.database import (
    Base,
    SessionLocal,
    engine,
)
from app.services.fixture_sync import sync_fixtures

import app.models


def run():
    Base.metadata.create_all(bind=engine)

    client = APIFootballClient()

    today = date.today().isoformat()

    print(f"Fetching fixtures for {today}...")

    data = client.get_fixtures_by_date(today)

    fixtures = data.get("response", [])

    print(f"Fixtures received: {len(fixtures)}")

    if not fixtures:
        print("No fixtures found.")
        return

    db = SessionLocal()

    try:
        synced = sync_fixtures(
            db=db,
            fixtures=fixtures,
        )

        print(
            f"Successfully synced {synced} fixtures."
        )

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    run()