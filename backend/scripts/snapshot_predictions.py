from datetime import datetime, timezone

from app.database.database import SessionLocal
from app.models.match import Match

from app.services.prediction_tracking import (
    create_prediction_snapshot,
)


def run():
    db = SessionLocal()

    now = datetime.now(
        timezone.utc
    )

    saved = 0
    unchanged = 0
    skipped = 0
    failed = 0

    try:
        matches = (
            db.query(Match)
            .filter(
                Match.match_date >= now
            )
            .order_by(
                Match.match_date.asc()
            )
            .limit(20)
            .all()
        )

        print()
        print("=" * 70)
        print(
            "ANALITIKO SMART PREDICTION SNAPSHOT"
        )
        print("=" * 70)

        print(
            f"Matches to check: {len(matches)}"
        )

        for match in matches:

            print()
            print(
                f"{match.home_team.name} "
                f"vs "
                f"{match.away_team.name}"
            )

            try:
                snapshot, status = (
                    create_prediction_snapshot(
                        db=db,
                        match=match,
                    )
                )

                if status == "saved":
                    db.commit()

                    saved += 1

                    print(
                        "NEW SNAPSHOT SAVED"
                    )

                    print(
                        f"Pick: "
                        f"{snapshot.main_pick}"
                    )

                    print(
                        f"Confidence: "
                        f"{snapshot.confidence}%"
                    )

                elif status == "unchanged":
                    db.rollback()

                    unchanged += 1

                    print(
                        "Prediction unchanged "
                        "- snapshot skipped"
                    )

                elif status in (
                    "no_odds",
                    "no_history",
                ):
                    db.rollback()

                    skipped += 1

                    print(
                        f"Skipped: {status}"
                    )

            except Exception as error:
                db.rollback()

                failed += 1

                print(
                    f"FAILED: {error}"
                )

        print()
        print("=" * 70)
        print("SNAPSHOT COMPLETE")
        print("=" * 70)

        print(
            f"Saved: {saved}"
        )

        print(
            f"Unchanged: {unchanged}"
        )

        print(
            f"Skipped: {skipped}"
        )

        print(
            f"Failed: {failed}"
        )

    finally:
        db.close()


if __name__ == "__main__":
    run()