from app.database.database import (
    SessionLocal,
)

from app.models.market import Market
from app.models.signal import Signal
from app.models.market_evaluation_snapshot import (
    MarketEvaluationSnapshot,
)

from app.services.market_policy import (
    MARKET_POLICIES,
    get_market_policy,
)


def run():

    db = SessionLocal()

    try:

        print()
        print("=" * 80)
        print(
            "ANALITIKO MARKET GOVERNANCE TEST"
        )
        print("=" * 80)

        failed = 0

        for code in (
            MARKET_POLICIES.keys()
        ):

            policy = (
                get_market_policy(
                    code
                )
            )

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

            print()
            print(
                f"{code}"
            )

            print(
                f"  Status: "
                f"{policy.status}"
            )

            print(
                f"  Signals allowed: "
                f"{policy.allow_signals}"
            )

            print(
                f"  Combinations allowed: "
                f"{policy.allow_combinations}"
            )

            if market is None:

                print(
                    "  [FAIL] Market missing"
                )

                failed += 1

                continue

            active_signals = (
                db.query(Signal)
                .filter(
                    Signal.market_id
                    == market.id,

                    Signal.active
                    .is_(True),
                )
                .count()
            )

            snapshots = (
                db.query(
                    MarketEvaluationSnapshot
                )
                .filter(
                    MarketEvaluationSnapshot.market_id
                    == market.id
                )
                .count()
            )

            print(
                f"  Active signals: "
                f"{active_signals}"
            )

            print(
                f"  Prospective snapshots: "
                f"{snapshots}"
            )

            if (
                not policy.allow_signals
                and active_signals > 0
            ):

                print(
                    "  [FAIL] Blocked market "
                    "still has active signals"
                )

                failed += 1

            else:

                print(
                    "  [OK]"
                )

        print()
        print("=" * 80)

        if failed == 0:

            print(
                "STATUS: OK"
            )

        else:

            print(
                f"STATUS: PARTIAL "
                f"({failed} failures)"
            )

        print("=" * 80)

    finally:

        db.close()


if __name__ == "__main__":
    run()