from datetime import datetime

from app.database.database import (
    SessionLocal,
)

from app.models.match import Match
from app.models.market import Market
from app.models.signal import Signal
from app.models.signal_intelligence import (
    SignalIntelligence,
)


def run():

    db = SessionLocal()

    now = datetime.utcnow()

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
                Signal.is_value.is_(True),
                Match.match_date > now,
            )
            .all()
        )

        markets = {
            row.id:
                row.code
            for row in (
                db.query(Market)
                .all()
            )
        }

        results = []

        for signal in signals:

            intelligence = (
                db.query(
                    SignalIntelligence
                )
                .filter(
                    SignalIntelligence.signal_id
                    == signal.id
                )
                .order_by(
                    SignalIntelligence
                    .calculated_at
                    .desc()
                )
                .first()
            )

            if intelligence is None:
                continue

            match = (
                db.query(Match)
                .filter(
                    Match.id
                    == signal.match_id
                )
                .first()
            )

            results.append(
                (
                    intelligence
                    .anomaly_score,

                    signal,

                    intelligence,

                    match,
                )
            )

        results.sort(
            key=lambda item:
                item[0],
            reverse=True,
        )

        print()
        print("=" * 110)
        print(
            "ANALITIKO VALUE ANOMALY AUDIT"
        )
        print("=" * 110)

        critical = 0
        high = 0
        watch = 0
        normal = 0

        for (
            _,
            signal,
            intelligence,
            match,
        ) in results:

            level = (
                intelligence
                .anomaly_level
            )

            if level == "CRITICAL":
                critical += 1

            elif level == "HIGH":
                high += 1

            elif level == "WATCH":
                watch += 1

            else:
                normal += 1

            print()
            print(
                f"{match.home_team.name} "
                f"vs "
                f"{match.away_team.name}"
            )

            print(
                f"  Market: "
                f"{markets.get(signal.market_id)} "
                f"{signal.selection}"
            )

            print(
                f"  Model: "
                f"{signal.model_probability:.2f}%"
            )

            print(
                f"  Calibrated: "
                f"{intelligence.calibrated_probability:.2f}%"
            )

            print(
                f"  Market probability: "
                f"{signal.market_probability}"
            )

            print(
                f"  Odds: "
                f"{signal.odds}"
            )

            print(
                f"  Bookmaker: "
                f"{signal.bookmaker}"
            )

            print(
                f"  Edge: "
                f"{signal.edge}"
            )

            print(
                f"  EV: "
                f"{signal.expected_value}"
            )

            print(
                f"  Quality: "
                f"{intelligence.quality_score:.2f}"
            )

            print(
                f"  Anomaly: "
                f"{intelligence.anomaly_score:.2f} "
                f"{level}"
            )

        print()
        print("=" * 110)
        print("SUMMARY")
        print("=" * 110)

        print(
            f"CRITICAL: {critical}"
        )

        print(
            f"HIGH:     {high}"
        )

        print(
            f"WATCH:    {watch}"
        )

        print(
            f"NORMAL:   {normal}"
        )

        print()
        print(
            "STATUS: OK"
        )

        print("=" * 110)

    finally:

        db.close()


if __name__ == "__main__":
    run()