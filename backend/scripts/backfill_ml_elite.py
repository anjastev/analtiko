from app.database.database import (
    SessionLocal,
)

from app.models.ml_prediction_snapshot import (
    MLPredictionSnapshot,
)


ELITE_THRESHOLD = 50.0


def run():

    db = SessionLocal()

    updated = 0
    elite_count = 0
    strong_count = 0


    try:

        snapshots = (
            db.query(
                MLPredictionSnapshot
            )
            .all()
        )


        print()
        print("=" * 70)
        print(
            "ANALITIKO ML ELITE BACKFILL"
        )
        print("=" * 70)

        print(
            f"Snapshots: "
            f"{len(snapshots)}"
        )


        for snapshot in snapshots:

            # ================================================
            # ELITE
            # ================================================

            is_elite = (
                snapshot.analitiko_score
                >= ELITE_THRESHOLD
            )


            snapshot.elite_threshold = (
                ELITE_THRESHOLD
            )


            snapshot.is_elite_pick = (
                is_elite
            )


            # ================================================
            # CONFIDENCE LEVEL
            # ================================================

            if is_elite:

                snapshot.confidence_level = (
                    "ELITE"
                )

                elite_count += 1


            elif snapshot.is_strong_pick:

                snapshot.confidence_level = (
                    "STRONG"
                )

                strong_count += 1


            elif (
                snapshot.analitiko_score
                >= 40
            ):

                snapshot.confidence_level = (
                    "MEDIUM"
                )


            else:

                snapshot.confidence_level = (
                    "LOW"
                )


            updated += 1


        db.commit()


        print()
        print(
            f"Updated: "
            f"{updated}"
        )

        print(
            f"Elite: "
            f"{elite_count}"
        )

        print(
            f"Strong non-elite: "
            f"{strong_count}"
        )

        print()
        print(
            "Backfill complete."
        )

        print("=" * 70)


    except Exception:

        db.rollback()

        raise


    finally:

        db.close()


if __name__ == "__main__":
    run()