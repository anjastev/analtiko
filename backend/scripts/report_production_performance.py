from app.database.database import (
    SessionLocal,
)

from app.models.combination import (
    Combination,
)

from app.models.signal import Signal


def percentage(
    part,
    total,
):

    if total == 0:
        return 0.0

    return (
        part
        / total
        * 100.0
    )


def run():

    db = SessionLocal()

    try:

        signals = (
            db.query(Signal)
            .filter(
                Signal.is_value
                .is_(True),

                Signal.evaluated_at
                .isnot(None),
            )
            .all()
        )

        signal_wins = sum(
            1
            for row in signals
            if row.correct is True
        )

        signal_losses = sum(
            1
            for row in signals
            if row.correct is False
        )

        signal_profit = sum(
            float(
                row.profit
                or 0.0
            )
            for row in signals
        )

        combinations = (
            db.query(Combination)
            .filter(
                Combination.evaluated_at
                .isnot(None)
            )
            .all()
        )

        combo_wins = sum(
            1
            for row in combinations
            if row.status == "won"
        )

        combo_losses = sum(
            1
            for row in combinations
            if row.status == "lost"
        )

        combo_profit = sum(
            float(
                row.profit
                or 0.0
            )
            for row in combinations
        )

        print()
        print("=" * 100)
        print(
            "ANALITIKO PRODUCTION PERFORMANCE"
        )
        print("=" * 100)

        print()
        print(
            "VALUE SIGNALS"
        )

        print(
            f"Evaluated: "
            f"{len(signals)}"
        )

        print(
            f"Wins: "
            f"{signal_wins}"
        )

        print(
            f"Losses: "
            f"{signal_losses}"
        )

        print(
            f"Hit rate: "
            f"{percentage(signal_wins, len(signals)):.2f}%"
        )

        print(
            f"Profit: "
            f"{signal_profit:+.2f}u"
        )

        print(
            f"ROI: "
            f"{percentage(signal_profit, len(signals)):+.2f}%"
        )

        print()
        print(
            "COMBINATIONS"
        )

        print(
            f"Evaluated: "
            f"{len(combinations)}"
        )

        print(
            f"Wins: "
            f"{combo_wins}"
        )

        print(
            f"Losses: "
            f"{combo_losses}"
        )

        print(
            f"Hit rate: "
            f"{percentage(combo_wins, len(combinations)):.2f}%"
        )

        print(
            f"Profit: "
            f"{combo_profit:+.2f}u"
        )

        print(
            f"ROI: "
            f"{percentage(combo_profit, len(combinations)):+.2f}%"
        )

        print()
        print(
            "STATUS: OK"
        )

        print("=" * 100)

    finally:

        db.close()


if __name__ == "__main__":
    run()