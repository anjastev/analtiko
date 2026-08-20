from app.database.database import SessionLocal

from app.models.match import Match
from app.models.prediction_snapshot import PredictionSnapshot


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

    try:

        snapshots = (
            db.query(PredictionSnapshot)
            .filter(
                PredictionSnapshot.is_official == 1,
                PredictionSnapshot.actual_result.is_(None),
            )
            .order_by(
                PredictionSnapshot.created_at.asc()
            )
            .all()
        )

        print()
        print("=" * 70)
        print("ANALITIKO PREDICTION EVALUATION")
        print("=" * 70)

        print(
            f"Pending snapshots: {len(snapshots)}"
        )

        for snapshot in snapshots:

            match = (
                db.query(Match)
                .filter(
                    Match.id == snapshot.match_id
                )
                .first()
            )

            if not match:
                print()
                print(
                    f"Snapshot {snapshot.id}: "
                    f"match not found"
                )

                skipped += 1
                continue

            print()
            print(
                f"{match.home_team.name} "
                f"vs "
                f"{match.away_team.name}"
            )

            # ---------------------------------------------
            # Match must be finished
            # ---------------------------------------------

            if (
                match.status
                not in FINISHED_STATUSES
            ):
                print(
                    f"Skipped - status: {match.status}"
                )

                skipped += 1
                continue

            # ---------------------------------------------
            # Scores required
            # ---------------------------------------------

            if (
                match.home_score is None
                or match.away_score is None
            ):
                print(
                    "Skipped - final score missing"
                )

                skipped += 1
                continue

            home_score = match.home_score
            away_score = match.away_score

            # ---------------------------------------------
            # 1X2 RESULT
            # ---------------------------------------------

            actual_result = (
                get_actual_result(
                    home_score,
                    away_score,
                )
            )

            snapshot.actual_result = (
                actual_result
            )

            snapshot.result_correct = (
                1
                if snapshot.main_pick
                == actual_result
                else 0
            )

            # ---------------------------------------------
            # OVER 2.5
            # ---------------------------------------------

            total_goals = (
                home_score
                + away_score
            )

            actual_over_25 = (
                1
                if total_goals > 2.5
                else 0
            )

            snapshot.actual_over_25 = (
                actual_over_25
            )

            if snapshot.over_25 is not None:

                predicted_over_25 = (
                    1
                    if snapshot.over_25 >= 50
                    else 0
                )

                snapshot.over_25_correct = (
                    1
                    if predicted_over_25
                    == actual_over_25
                    else 0
                )

            # ---------------------------------------------
            # BTTS
            # ---------------------------------------------

            actual_btts = (
                1
                if (
                    home_score > 0
                    and away_score > 0
                )
                else 0
            )

            snapshot.actual_btts = (
                actual_btts
            )

            if snapshot.btts_yes is not None:

                predicted_btts = (
                    1
                    if snapshot.btts_yes >= 50
                    else 0
                )

                snapshot.btts_correct = (
                    1
                    if predicted_btts
                    == actual_btts
                    else 0
                )

            db.commit()

            evaluated += 1

            print(
                f"Final score: "
                f"{home_score}-{away_score}"
            )

            print(
                f"Prediction: "
                f"{snapshot.main_pick}"
            )

            print(
                f"Actual: "
                f"{actual_result}"
            )

            print(
                "Result correct: "
                f"{'YES' if snapshot.result_correct else 'NO'}"
            )

            if snapshot.over_25 is not None:

                print(
                    f"Over 2.5: "
                    f"{snapshot.over_25}% "
                    f"-> "
                    f"{'YES' if snapshot.over_25_correct else 'NO'}"
                )

            if snapshot.btts_yes is not None:

                print(
                    f"BTTS: "
                    f"{snapshot.btts_yes}% "
                    f"-> "
                    f"{'YES' if snapshot.btts_correct else 'NO'}"
                )

        print()
        print("=" * 70)
        print("EVALUATION COMPLETE")
        print("=" * 70)

        print(
            f"Evaluated: {evaluated}"
        )

        print(
            f"Skipped: {skipped}"
        )

    except Exception:

        db.rollback()
        raise

    finally:

        db.close()


if __name__ == "__main__":
    run()