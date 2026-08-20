from datetime import (
    datetime,
    timezone,
)

from app.database.database import (
    SessionLocal,
)

from app.models.match import Match

from app.models.ml_prediction_snapshot import (
    MLPredictionSnapshot,
)


FINISHED_STATUSES = {
    "FT",
    "AET",
    "PEN",
}


def get_actual_result(
    home_score: int,
    away_score: int,
) -> str:

    if home_score > away_score:
        return "HOME"

    if home_score < away_score:
        return "AWAY"

    return "DRAW"


def run():

    db = SessionLocal()

    evaluated = 0
    skipped = 0
    failed = 0


    try:

        snapshots = (
            db.query(
                MLPredictionSnapshot
            )
            .filter(
                MLPredictionSnapshot.correct
                .is_(None)
            )
            .order_by(
                MLPredictionSnapshot
                .created_at
                .asc()
            )
            .all()
        )


        print()
        print("=" * 70)
        print(
            "ANALITIKO ML PREDICTION EVALUATION"
        )
        print("=" * 70)

        print(
            f"Pending snapshots: "
            f"{len(snapshots)}"
        )


        for snapshot in snapshots:

            try:

                match = (
                    db.query(Match)
                    .filter(
                        Match.id
                        == snapshot.match_id
                    )
                    .first()
                )


                if not match:

                    skipped += 1

                    print()
                    print(
                        f"Match "
                        f"{snapshot.match_id}"
                    )

                    print(
                        "Skipped: match_not_found"
                    )

                    continue


                print()
                print(
                    f"{match.home_team.name} "
                    f"vs "
                    f"{match.away_team.name}"
                )


                if (
                    match.status
                    not in FINISHED_STATUSES
                ):

                    skipped += 1

                    print(
                        f"Skipped: "
                        f"status={match.status}"
                    )

                    continue


                if (
                    match.home_score
                    is None
                    or
                    match.away_score
                    is None
                ):

                    skipped += 1

                    print(
                        "Skipped: missing_score"
                    )

                    continue


                actual_result = (
                    get_actual_result(
                        match.home_score,
                        match.away_score,
                    )
                )


                correct = (
                    snapshot.pick
                    == actual_result
                )


                snapshot.actual_result = (
                    actual_result
                )


                snapshot.correct = (
                    correct
                )


                snapshot.evaluated_at = (
                    datetime.now(
                        timezone.utc
                    )
                )


                db.commit()

                evaluated += 1


                print(
                    f"Prediction: "
                    f"{snapshot.pick}"
                )

                print(
                    f"Actual: "
                    f"{actual_result}"
                )

                print(
                    f"Score: "
                    f"{match.home_score}"
                    f"-"
                    f"{match.away_score}"
                )

                print(
                    f"Strong: "
                    f"{snapshot.is_strong_pick}"
                )

                print(
                    f"Elite: "
                    f"{snapshot.is_elite_pick}"
                )

                print(
                    f"Level: "
                    f"{snapshot.confidence_level}"
                )

                print(
                    f"Analitiko Score: "
                    f"{snapshot.analitiko_score}"
                )

                print(
                    "Result: "
                    f"{'CORRECT' if correct else 'WRONG'}"
                )


            except Exception as error:

                db.rollback()

                failed += 1


                print(
                    f"FAILED: "
                    f"{error}"
                )


        print()
        print("=" * 70)
        print(
            "ML EVALUATION COMPLETE"
        )
        print("=" * 70)

        print(
            f"Evaluated: "
            f"{evaluated}"
        )

        print(
            f"Skipped: "
            f"{skipped}"
        )

        print(
            f"Failed: "
            f"{failed}"
        )

        print("=" * 70)


    finally:

        db.close()


if __name__ == "__main__":
    run()