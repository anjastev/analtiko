from datetime import (
    datetime,
    timezone,
)

from app.database.database import (
    SessionLocal,
)

from app.models.match import Match
from app.models.signal import Signal


MIN_EDGE = 5.0


def run():

    db = SessionLocal()

    now = datetime.now(
        timezone.utc
    )

    try:

        signals = (
            db.query(Signal)
            .join(
                Match,
                Match.id
                == Signal.match_id,
            )
            .filter(
                Signal.active.is_(True),

                Match.match_date
                >= now,
            )
            .all()
        )

        priced = 0
        value = 0
        unpriced = 0

        print()
        print("=" * 100)
        print(
            "ANALITIKO VALUE PIPELINE TEST"
        )
        print("=" * 100)

        for signal in signals:

            if (
                signal.odds is None
                or
                signal.edge is None
                or
                signal.market_probability is None
            ):

                unpriced += 1
                continue

            priced += 1

            if (
                float(
                    signal.edge
                )
                >= MIN_EDGE
            ):

                value += 1

        print(
            f"Active signals: "
            f"{len(signals)}"
        )

        print(
            f"Priced signals: "
            f"{priced}"
        )

        print(
            f"Unpriced signals: "
            f"{unpriced}"
        )

        print(
            f"VALUE edge >= "
            f"{MIN_EDGE:.1f}%: "
            f"{value}"
        )

        print()
        print("=" * 100)

        if (
            len(signals) == 0
        ):

            print(
                "STATUS: NO ACTIVE SIGNALS"
            )

        elif priced == 0:

            print(
                "STATUS: WAITING FOR DIRECT ODDS"
            )

        else:

            print(
                "STATUS: OK"
            )

        print("=" * 100)

    finally:

        db.close()


if __name__ == "__main__":
    run()