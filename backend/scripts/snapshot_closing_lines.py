from datetime import datetime

from app.database.database import (
    SessionLocal,
)

from app.models.clv_snapshot import (
    CLVSnapshot,
)

from app.models.match import Match
from app.models.signal import Signal

from app.services.clv_service import (
    calculate_clv,
    find_closing_odds,
)


def run():

    db = SessionLocal()

    now = datetime.utcnow()

    created = 0
    waiting = 0

    try:

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

                Signal.odds
                .isnot(None),

                Match.match_date
                <= now,
            )
            .all()
        )

        print()
        print("=" * 100)
        print(
            "ANALITIKO CLOSING LINE SNAPSHOT"
        )
        print("=" * 100)

        for signal in signals:

            existing = (
                db.query(
                    CLVSnapshot
                )
                .filter(
                    CLVSnapshot.signal_id
                    == signal.id
                )
                .first()
            )

            if existing is not None:
                continue

            match = (
                db.query(Match)
                .filter(
                    Match.id
                    == signal.match_id
                )
                .first()
            )

            if match is None:
                continue

            closing = (
                find_closing_odds(
                    db,
                    signal=signal,
                    kickoff=(
                        match.match_date
                    ),
                )
            )

            if closing is None:

                waiting += 1

                db.add(
                    CLVSnapshot(
                        signal_id=(
                            signal.id
                        ),

                        match_id=(
                            signal.match_id
                        ),

                        bookmaker=(
                            signal.bookmaker
                        ),

                        recommended_odds=(
                            signal.odds
                        ),

                        recommended_probability=(
                            signal.market_probability
                        ),

                        recommendation_time=(
                            signal.odds_recorded_at
                        ),

                        status="NO_CLOSE",
                    )
                )

                created += 1
                continue

            closing_odds = float(
                closing.odds
            )

            closing_probability = (
                100.0
                / closing_odds
            )

            clv = (
                calculate_clv(
                    float(
                        signal.odds
                    ),
                    closing_odds,
                )
            )

            db.add(
                CLVSnapshot(
                    signal_id=(
                        signal.id
                    ),

                    match_id=(
                        signal.match_id
                    ),

                    bookmaker=(
                        signal.bookmaker
                    ),

                    recommended_odds=(
                        signal.odds
                    ),

                    closing_odds=(
                        closing_odds
                    ),

                    recommended_probability=(
                        signal.market_probability
                    ),

                    closing_probability=(
                        closing_probability
                    ),

                    clv_pct=(
                        clv
                    ),

                    recommendation_time=(
                        signal.odds_recorded_at
                    ),

                    closing_time=(
                        closing.recorded_at
                    ),

                    status="CLOSED",
                )
            )

            created += 1

        db.commit()

        print(
            f"Snapshots created: "
            f"{created}"
        )

        print(
            f"No closing quote: "
            f"{waiting}"
        )

        print()
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