from datetime import datetime

from app.database.database import (
    SessionLocal,
)

from app.models.combination import (
    Combination,
)

from app.models.combination_selection import (
    CombinationSelection,
)

from app.models.signal import Signal


def run():

    db = SessionLocal()

    evaluated = 0
    won = 0
    lost = 0
    pending = 0

    try:

        combinations = (
            db.query(Combination)
            .filter(
                Combination.status
                == "pending"
            )
            .all()
        )

        print()
        print("=" * 100)
        print(
            "ANALITIKO COMBINATION EVALUATION"
        )
        print("=" * 100)

        for combination in combinations:

            selections = (
                db.query(
                    CombinationSelection
                )
                .filter(
                    CombinationSelection.combination_id
                    == combination.id
                )
                .all()
            )

            if not selections:
                continue

            all_finished = True
            any_loss = False

            for selection in selections:

                signal = (
                    db.query(Signal)
                    .filter(
                        Signal.id
                        == selection.signal_id
                    )
                    .first()
                )

                if (
                    signal is None
                    or
                    signal.evaluated_at
                    is None
                    or
                    signal.correct
                    is None
                ):

                    all_finished = False
                    continue

                selection.actual_result = (
                    signal.actual_result
                )

                selection.correct = (
                    signal.correct
                )

                selection.evaluated_at = (
                    signal.evaluated_at
                )

                if signal.correct:

                    selection.profit = (
                        round(
                            float(
                                selection.odds
                            )
                            - 1.0,
                            4,
                        )
                    )

                else:

                    selection.profit = (
                        -1.0
                    )

                    any_loss = True

            if not all_finished:

                pending += 1
                continue

            if any_loss:

                combination.status = (
                    "lost"
                )

                combination.profit = (
                    -1.0
                )

                combination.roi = (
                    -100.0
                )

                lost += 1

            else:

                combination.status = (
                    "won"
                )

                if (
                    combination.total_odds
                    is not None
                ):

                    profit = (
                        float(
                            combination.total_odds
                        )
                        - 1.0
                    )

                else:

                    product = 1.0

                    for selection in selections:

                        product *= float(
                            selection.odds
                        )

                    combination.total_odds = (
                        round(
                            product,
                            4,
                        )
                    )

                    profit = (
                        product
                        - 1.0
                    )

                combination.profit = (
                    round(
                        profit,
                        4,
                    )
                )

                combination.roi = (
                    round(
                        profit
                        * 100.0,
                        4,
                    )
                )

                won += 1

            combination.evaluated_at = (
                datetime.utcnow()
            )

            evaluated += 1

            print(
                f"[{combination.status.upper()}] "
                f"Combination "
                f"{combination.id} | "
                f"{combination.strategy} | "
                f"profit="
                f"{combination.profit:+.2f}u"
            )

        db.commit()

        evaluated_rows = (
            db.query(Combination)
            .filter(
                Combination.evaluated_at
                .isnot(None)
            )
            .all()
        )

        total_profit = sum(
            float(
                combination.profit
                or 0.0
            )
            for combination
            in evaluated_rows
        )

        count = len(
            evaluated_rows
        )

        roi = (
            total_profit
            / count
            * 100.0
            if count
            else 0.0
        )

        print()
        print("=" * 100)
        print(
            "COMBINATION EVALUATION SUMMARY"
        )
        print("=" * 100)

        print(
            f"Evaluated this run: "
            f"{evaluated}"
        )

        print(
            f"Won: "
            f"{won}"
        )

        print(
            f"Lost: "
            f"{lost}"
        )

        print(
            f"Still pending: "
            f"{pending}"
        )

        print(
            f"Historical evaluated: "
            f"{count}"
        )

        print(
            f"Profit @ 1u: "
            f"{total_profit:+.2f}u"
        )

        print(
            f"ROI: "
            f"{roi:+.2f}%"
        )

        print(
            "STATUS: OK"
        )

        print("=" * 100)

    except Exception:

        db.rollback()
        raise

    finally:

        db.close()


if __name__ == "__main__":
    run()