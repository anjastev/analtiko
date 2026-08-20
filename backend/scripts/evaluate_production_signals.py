from datetime import datetime

from app.database.database import (
    SessionLocal,
)

from app.models.market import Market
from app.models.match import Match
from app.models.signal import Signal


FINISHED_STATUSES = {
    "FT",
    "AET",
    "PEN",
}


def get_match_result(
    match,
):

    if (
        match.home_score is None
        or match.away_score is None
    ):

        return None

    if (
        match.home_score
        > match.away_score
    ):

        return "HOME"

    if (
        match.home_score
        < match.away_score
    ):

        return "AWAY"

    return "DRAW"


def evaluate_dc(
    selection,
    actual_result,
):

    if selection == "1X":

        return (
            actual_result
            in {
                "HOME",
                "DRAW",
            }
        )

    if selection == "X2":

        return (
            actual_result
            in {
                "DRAW",
                "AWAY",
            }
        )

    if selection == "12":

        return (
            actual_result
            in {
                "HOME",
                "AWAY",
            }
        )

    return None


def run():

    db = SessionLocal()

    evaluated = 0
    wins = 0
    losses = 0
    skipped = 0

    try:

        markets = (
            db.query(Market)
            .filter(
                Market.sport
                == "football"
            )
            .all()
        )

        market_map = {
            market.id:
                market.code
            for market in markets
        }

        signals = (
            db.query(Signal)
            .join(
                Match,
                Match.id
                == Signal.match_id,
            )
            .filter(
                Signal.is_value
                .is_(True),

                Signal.evaluated_at
                .is_(None),

                Match.status.in_(
                    FINISHED_STATUSES
                ),
            )
            .all()
        )

        print()
        print("=" * 100)
        print(
            "ANALITIKO PRODUCTION SIGNAL EVALUATION"
        )
        print("=" * 100)

        for signal in signals:

            match = (
                db.query(Match)
                .filter(
                    Match.id
                    == signal.match_id
                )
                .first()
            )

            if match is None:

                skipped += 1
                continue

            actual_result = (
                get_match_result(
                    match
                )
            )

            if actual_result is None:

                skipped += 1
                continue

            market_code = (
                market_map.get(
                    signal.market_id
                )
            )

            correct = None

            if market_code == "DC":

                correct = (
                    evaluate_dc(
                        signal.selection,
                        actual_result,
                    )
                )

            if correct is None:

                skipped += 1
                continue

            signal.actual_result = (
                actual_result
            )

            signal.correct = (
                bool(
                    correct
                )
            )

            signal.evaluated_at = (
                datetime.utcnow()
            )

            if correct:

                wins += 1

                profit = (
                    float(
                        signal.odds
                    )
                    - 1.0
                )

            else:

                losses += 1
                profit = -1.0

            signal.profit = (
                round(
                    profit,
                    4,
                )
            )

            # One unit stake.
            signal.roi = (
                round(
                    profit
                    * 100.0,
                    4,
                )
            )

            evaluated += 1

            print(
                f"[{'WIN' if correct else 'LOSS'}] "
                f"{match.home_team.name} "
                f"vs "
                f"{match.away_team.name} | "
                f"{market_code} "
                f"{signal.selection} | "
                f"odds={signal.odds}"
            )

        db.commit()

        total_profit = (
            db.query(Signal)
            .filter(
                Signal.is_value
                .is_(True),

                Signal.evaluated_at
                .isnot(None),
            )
            .all()
        )

        total_profit_value = sum(
            float(
                signal.profit
                or 0.0
            )
            for signal
            in total_profit
        )

        total_bets = len(
            total_profit
        )

        roi = (
            total_profit_value
            / total_bets
            * 100.0
            if total_bets
            else 0.0
        )

        print()
        print("=" * 100)
        print(
            "SIGNAL EVALUATION SUMMARY"
        )
        print("=" * 100)

        print(
            f"Evaluated this run: "
            f"{evaluated}"
        )

        print(
            f"Wins: "
            f"{wins}"
        )

        print(
            f"Losses: "
            f"{losses}"
        )

        print(
            f"Skipped: "
            f"{skipped}"
        )

        print(
            f"All evaluated VALUE bets: "
            f"{total_bets}"
        )

        print(
            f"Total profit @ 1u: "
            f"{total_profit_value:+.2f}u"
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