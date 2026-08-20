from app.database.database import (
    SessionLocal,
)

from app.models.market import Market
from app.models.signal import Signal

from app.services.market_policy import (
    MARKET_POLICIES,
    get_market_policy,
)


def run():

    db = SessionLocal()

    deactivated = 0
    kept = 0

    try:

        markets = (
            db.query(Market)
            .filter(
                Market.sport
                == "football",

                Market.code.in_(
                    list(
                        MARKET_POLICIES.keys()
                    )
                ),
            )
            .all()
        )

        print()
        print("=" * 80)
        print(
            "ANALITIKO MARKET POLICY APPLICATION"
        )
        print("=" * 80)

        for market in markets:

            policy = (
                get_market_policy(
                    market.code
                )
            )

            active_signals = (
                db.query(Signal)
                .filter(
                    Signal.market_id
                    == market.id,

                    Signal.active
                    .is_(True),
                )
                .all()
            )

            print()
            print(
                f"{market.code}: "
                f"{policy.status}"
            )

            print(
                f"Reason: "
                f"{policy.reason}"
            )

            if policy.allow_signals:

                kept += len(
                    active_signals
                )

                print(
                    f"Active signals kept: "
                    f"{len(active_signals)}"
                )

                continue

            for signal in active_signals:

                signal.active = False
                deactivated += 1

            print(
                f"Signals deactivated: "
                f"{len(active_signals)}"
            )

        db.commit()

        print()
        print("=" * 80)

        print(
            f"Kept: "
            f"{kept}"
        )

        print(
            f"Deactivated: "
            f"{deactivated}"
        )

        print(
            "STATUS: OK"
        )

        print("=" * 80)

    except Exception:

        db.rollback()
        raise

    finally:

        db.close()


if __name__ == "__main__":
    run()