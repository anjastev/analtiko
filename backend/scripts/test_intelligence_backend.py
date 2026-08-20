from app.database.database import (
    SessionLocal,
)

from app.models.combination import Combination
from app.models.combination_selection import (
    CombinationSelection,
)
from app.models.data_source import DataSource
from app.models.market import Market
from app.models.market_odds import MarketOdds
from app.models.market_prediction import (
    MarketPrediction,
)
from app.models.signal import Signal
from app.models.sport import Sport


def print_check(
    label: str,
    value,
    minimum: int = 1,
):

    ok = (
        value >= minimum
    )

    status = (
        "OK"
        if ok
        else "WARN"
    )

    print(
        f"[{status}] "
        f"{label}: "
        f"{value}"
    )

    return ok


def run():

    db = SessionLocal()

    checks = []

    try:

        print()
        print("=" * 80)
        print(
            "ANALITIKO INTELLIGENCE BACKEND TEST"
        )
        print("=" * 80)

        sports = (
            db.query(Sport)
            .count()
        )

        sources = (
            db.query(DataSource)
            .count()
        )

        markets = (
            db.query(Market)
            .count()
        )

        predictions = (
            db.query(
                MarketPrediction
            )
            .count()
        )

        signals = (
            db.query(Signal)
            .count()
        )

        market_odds = (
            db.query(MarketOdds)
            .count()
        )

        combinations = (
            db.query(Combination)
            .count()
        )

        combination_selections = (
            db.query(
                CombinationSelection
            )
            .count()
        )

        checks.append(
            print_check(
                "Sports",
                sports,
            )
        )

        checks.append(
            print_check(
                "Data sources",
                sources,
            )
        )

        checks.append(
            print_check(
                "Markets",
                markets,
            )
        )

        checks.append(
            print_check(
                "Market predictions",
                predictions,
            )
        )

        checks.append(
            print_check(
                "Signals",
                signals,
            )
        )

        checks.append(
            print_check(
                "Market odds",
                market_odds,
            )
        )

        checks.append(
            print_check(
                "Combinations",
                combinations,
            )
        )

        checks.append(
            print_check(
                "Combination selections",
                combination_selections,
            )
        )

        # ====================================================
        # SIGNATURE TEST
        # ====================================================

        signed = (
            db.query(Combination)
            .filter(
                Combination.signature
                .isnot(None)
            )
            .count()
        )

        print()

        if signed > 0:

            print(
                f"[OK] Signed combinations: "
                f"{signed}"
            )

            checks.append(
                True
            )

        else:

            print(
                "[WARN] No signed combinations yet."
            )

            checks.append(
                False
            )

        # ====================================================
        # DUPLICATE SIGNATURE CHECK
        # ====================================================

        combinations_with_signature = (
            db.query(Combination)
            .filter(
                Combination.signature
                .isnot(None)
            )
            .all()
        )

        signatures = [
            row.signature
            for row
            in combinations_with_signature
        ]

        duplicate_count = (
            len(signatures)
            - len(set(signatures))
        )

        print()

        if duplicate_count == 0:

            print(
                "[OK] Duplicate combination "
                "signatures: 0"
            )

            checks.append(
                True
            )

        else:

            print(
                f"[WARN] Duplicate combination "
                f"signatures: "
                f"{duplicate_count}"
            )

            checks.append(
                False
            )

        # ====================================================
        # FINAL
        # ====================================================

        passed = sum(
            1
            for check in checks
            if check
        )

        total = len(
            checks
        )

        print()
        print("=" * 80)

        print(
            f"Checks passed: "
            f"{passed}/{total}"
        )

        if passed == total:

            print(
                "STATUS: OK"
            )

        else:

            print(
                "STATUS: PARTIAL"
            )

        print("=" * 80)

    finally:

        db.close()


if __name__ == "__main__":
    run()