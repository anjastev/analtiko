from datetime import datetime, timezone, timedelta

from app.database.database import SessionLocal

from app.models.match import Match
from app.models.prediction_snapshot import PredictionSnapshot

from app.services.prediction_tracking import (
    create_prediction_snapshot,
)


MIN_MINUTES_BEFORE_KICKOFF = 20
MAX_MINUTES_BEFORE_KICKOFF = 90


def run():
    db = SessionLocal()

    now = datetime.now(
        timezone.utc
    )

    window_start = (
        now
        + timedelta(
            minutes=MIN_MINUTES_BEFORE_KICKOFF
        )
    )

    window_end = (
        now
        + timedelta(
            minutes=MAX_MINUTES_BEFORE_KICKOFF
        )
    )

    created = 0
    skipped = 0
    failed = 0

    try:

        matches = (
            db.query(Match)
            .filter(
                Match.match_date >= window_start,
                Match.match_date <= window_end,
            )
            .order_by(
                Match.match_date.asc()
            )
            .all()
        )

        print()
        print("=" * 70)
        print("ANALITIKO OFFICIAL PREDICTIONS")
        print("=" * 70)

        print(
            f"Window: "
            f"{MIN_MINUTES_BEFORE_KICKOFF}"
            f"-"
            f"{MAX_MINUTES_BEFORE_KICKOFF} "
            f"minutes before kickoff"
        )

        print(
            f"Matches found: {len(matches)}"
        )

        for match in matches:

            print()
            print(
                f"{match.home_team.name} "
                f"vs "
                f"{match.away_team.name}"
            )

            existing_official = (
                db.query(
                    PredictionSnapshot
                )
                .filter(
                    PredictionSnapshot.match_id
                    == match.id,

                    PredictionSnapshot.is_official
                    == 1,
                )
                .first()
            )

            if existing_official:

                skipped += 1

                print(
                    "Official prediction "
                    "already exists."
                )

                continue

            try:

                snapshot, status = (
                    create_prediction_snapshot(
                        db=db,
                        match=match,
                    )
                )

                if status in (
                    "no_odds",
                    "no_history",
                ):

                    db.rollback()

                    skipped += 1

                    print(
                        f"Skipped: {status}"
                    )

                    continue

                # If prediction was unchanged,
                # create_prediction_snapshot can
                # return the previous snapshot.
                #
                # We do NOT want to mark an old
                # snapshot as official because it
                # may have been created hours ago.
                #
                # Therefore create a fresh copy.

                official = (
                    PredictionSnapshot(
                        match_id=match.id,

                        main_pick=
                            snapshot.main_pick,

                        confidence=
                            snapshot.confidence,

                        home_win=
                            snapshot.home_win,

                        draw=
                            snapshot.draw,

                        away_win=
                            snapshot.away_win,

                        over_25=
                            snapshot.over_25,

                        btts_yes=
                            snapshot.btts_yes,

                        is_official=1,

                        official_at=
                            datetime.utcnow(),
                    )
                )

                db.add(official)

                db.commit()

                created += 1

                print(
                    "OFFICIAL PREDICTION SAVED"
                )

                print(
                    f"Pick: "
                    f"{official.main_pick}"
                )

                print(
                    f"Confidence: "
                    f"{official.confidence}%"
                )

            except Exception as error:

                db.rollback()

                failed += 1

                print(
                    f"FAILED: {error}"
                )

        print()
        print("=" * 70)
        print("OFFICIAL PREDICTIONS COMPLETE")
        print("=" * 70)

        print(
            f"Created: {created}"
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