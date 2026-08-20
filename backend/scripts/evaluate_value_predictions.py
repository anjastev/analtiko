from datetime import datetime

from app.database.database import (
    SessionLocal,
)

from app.models.match import Match

from app.models.value_prediction_snapshot import (
    ValuePredictionSnapshot,
)


# ============================================================
# HELPERS
# ============================================================

def determine_result(
    home_score,
    away_score,
):

    if (
        home_score is None
        or away_score is None
    ):

        return None


    if (
        home_score
        > away_score
    ):

        return "HOME"


    if (
        away_score
        > home_score
    ):

        return "AWAY"


    return "DRAW"


# ============================================================
# MAIN
# ============================================================

def run():

    print()
    print("=" * 100)
    print(
        "EVALUATE VALUE PREDICTIONS"
    )
    print("=" * 100)


    db = SessionLocal()


    try:

        snapshots = (
            db.query(
                ValuePredictionSnapshot
            )
            .filter(
                ValuePredictionSnapshot
                .actual_result
                .is_(
                    None
                )
            )
            .order_by(
                ValuePredictionSnapshot
                .created_at
                .asc()
            )
            .all()
        )


        print(
            f"Pending snapshots: "
            f"{len(snapshots)}"
        )


        evaluated = 0
        correct_count = 0
        total_profit = 0.0


        for snapshot in snapshots:

            match = (
                db.query(
                    Match
                )
                .filter(
                    Match.id
                    == snapshot.match_id
                )
                .first()
            )


            if match is None:

                continue


            # Adapt these two names only if your
            # Match model uses different score fields.

            home_score = getattr(
                match,
                "home_score",
                None,
            )

            away_score = getattr(
                match,
                "away_score",
                None,
            )


            actual_result = (
                determine_result(
                    home_score,
                    away_score,
                )
            )


            if actual_result is None:

                continue


            correct = (
                snapshot.value_pick
                == actual_result
            )


            if correct:

                profit = (
                    float(
                        snapshot.market_odds
                    )
                    - 1.0
                )

            else:

                profit = -1.0


            roi = (
                profit
                * 100
            )


            snapshot.actual_result = (
                actual_result
            )

            snapshot.correct = (
                correct
            )

            snapshot.profit = (
                profit
            )

            snapshot.roi = (
                roi
            )

            snapshot.evaluated_at = (
                datetime.utcnow()
            )


            evaluated += 1

            total_profit += (
                profit
            )


            if correct:

                correct_count += 1


            print()
            print(
                f"Match {match.id}"
            )

            print(
                f"{match.home_team.name}"
                f" vs "
                f"{match.away_team.name}"
            )

            print(
                f"Pick: "
                f"{snapshot.value_pick}"
            )

            print(
                f"Actual: "
                f"{actual_result}"
            )

            print(
                f"Correct: "
                f"{correct}"
            )

            print(
                f"Profit: "
                f"{profit:+.2f} units"
            )


        db.commit()


        print()
        print("=" * 100)

        print(
            f"Evaluated: "
            f"{evaluated}"
        )


        if evaluated > 0:

            accuracy = (
                correct_count
                / evaluated
                * 100
            )

            roi = (
                total_profit
                / evaluated
                * 100
            )

            print(
                f"Correct: "
                f"{correct_count}"
            )

            print(
                f"Accuracy: "
                f"{accuracy:.1f}%"
            )

            print(
                f"Profit: "
                f"{total_profit:+.2f} units"
            )

            print(
                f"ROI: "
                f"{roi:+.1f}%"
            )


        print("=" * 100)


    except Exception:

        db.rollback()
        raise


    finally:

        db.close()


if __name__ == "__main__":
    run()