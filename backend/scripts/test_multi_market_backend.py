from app.database.database import (
    SessionLocal,
)

from app.models.combination import (
    Combination,
)
from app.models.market import Market
from app.models.market_prediction import (
    MarketPrediction,
)
from app.models.signal import Signal


MARKETS = [
    "DC",
    "OU_25",
    "BTTS",
]


def run():

    db = SessionLocal()

    try:

        print()
        print("=" * 80)
        print(
            "ANALITIKO MULTI-MARKET BACKEND TEST"
        )
        print("=" * 80)

        passed = 0
        total = 0

        for code in MARKETS:

            total += 1

            market = (
                db.query(Market)
                .filter(
                    Market.sport
                    == "football",

                    Market.code
                    == code,
                )
                .first()
            )

            if market:

                print(
                    f"[OK] Market "
                    f"{code}"
                )

                passed += 1

            else:

                print(
                    f"[FAIL] Market "
                    f"{code}"
                )

                continue

            total += 1

            predictions = (
                db.query(
                    MarketPrediction
                )
                .filter(
                    MarketPrediction.market_id
                    == market.id
                )
                .count()
            )

            if predictions > 0:

                print(
                    f"[OK] "
                    f"{code} predictions: "
                    f"{predictions}"
                )

                passed += 1

            else:

                print(
                    f"[WARN] "
                    f"{code} predictions: 0"
                )

            total += 1

            signals = (
                db.query(Signal)
                .filter(
                    Signal.market_id
                    == market.id
                )
                .count()
            )

            if signals > 0:

                print(
                    f"[OK] "
                    f"{code} signals: "
                    f"{signals}"
                )

                passed += 1

            else:

                print(
                    f"[WARN] "
                    f"{code} signals: 0"
                )

        total += 1

        multi = (
            db.query(Combination)
            .filter(
                Combination.name.like(
                    "%Multi-Market%"
                )
            )
            .count()
        )

        if multi > 0:

            print(
                f"[OK] "
                f"Multi-market combinations: "
                f"{multi}"
            )

            passed += 1

        else:

            print(
                "[WARN] "
                "Multi-market combinations: 0"
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