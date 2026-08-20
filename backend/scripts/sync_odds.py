from datetime import datetime, timedelta, timezone

from app.collectors.api_football import APIFootballClient
from app.database.database import SessionLocal
from app.models.match import Match
from app.services.odds_sync import sync_odds_for_match
import time

def run():
    db = SessionLocal()

    client = APIFootballClient()

    now = datetime.now(timezone.utc)

    end = now + timedelta(days=2)

    saved_count = 0
    unchanged_count = 0
    no_odds_count = 0
    failed_count = 0

    try:
        matches = (
            db.query(Match)
            .filter(
                Match.external_id.isnot(None),
                Match.match_date >= now,
                Match.match_date <= end,
            )
            .order_by(
                Match.match_date.asc()
            )
            .limit(10)
            .all()
        )

        print()
        print("=" * 60)
        print("ANALITIKO ODDS SYNC")
        print("=" * 60)

        print(
            f"Checking {len(matches)} matches..."
        )

        for match in matches:

            print()
            print(
                f"{match.home_team.name} "
                f"vs "
                f"{match.away_team.name}"
            )

            print(
                f"Fixture ID: "
                f"{match.external_id}"
            )

            try:
                snapshot, status = (
                    sync_odds_for_match(
                        db=db,
                        client=client,
                        match=match,
                    )
                )

                if status == "saved":
                    db.commit()

                    saved_count += 1

                    print("NEW ODDS SAVED")

                    print(
                        f"Bookmaker: "
                        f"{snapshot.bookmaker}"
                    )

                    print(
                        "1/X/2: "
                        f"{snapshot.home_win} / "
                        f"{snapshot.draw} / "
                        f"{snapshot.away_win}"
                    )

                elif status == "unchanged":
                    db.rollback()

                    unchanged_count += 1

                    print(
                        "Odds unchanged - skipped"
                    )

                elif status in (
                    "no_odds",
                    "incomplete_odds",
                    "no_external_id",
                ):
                    db.rollback()

                    no_odds_count += 1

                    print(
                        f"No usable odds "
                        f"({status})"
                    )

            except Exception as error:
                db.rollback()

                failed_count += 1

                print(
                    f"FAILED: {error}"
                )
        time.sleep(7)
        print()
        print("=" * 60)
        print("ODDS SYNC COMPLETE")
        print("=" * 60)

        print(
            f"New snapshots: {saved_count}"
        )

        print(
            f"Unchanged: {unchanged_count}"
        )

        print(
            f"No odds: {no_odds_count}"
        )

        print(
            f"Failed: {failed_count}"
        )

        print("=" * 60)

    finally:
        db.close()


if __name__ == "__main__":
    run()