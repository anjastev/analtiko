from datetime import datetime

from app.database.database import (
    SessionLocal,
)

from app.models.match import Match

from app.models.signal_intelligence import (
    SignalIntelligence,
)


def run():

    db = SessionLocal()

    now = datetime.utcnow()

    try:

        rows = (
            db.query(
                SignalIntelligence
            )
            .join(
                Match,
                Match.id
                == SignalIntelligence.match_id,
            )
            .filter(
                Match.match_date
                > now
            )
            .all()
        )

        eligible = [
            row
            for row in rows
            if row.production_eligible
        ]

        tiers = {
            "A+": 0,
            "A": 0,
            "B": 0,
            "C": 0,
            "D": 0,
        }

        for row in rows:

            tiers[
                row.quality_tier
            ] = (
                tiers.get(
                    row.quality_tier,
                    0,
                )
                + 1
            )

        avg_quality = (
            sum(
                row.quality_score
                for row in rows
            )
            / len(rows)
            if rows
            else 0.0
        )

        avg_uncertainty = (
            sum(
                row.uncertainty
                for row in rows
            )
            / len(rows)
            if rows
            else 0.0
        )

        print()
        print("=" * 100)
        print(
            "ANALITIKO SIGNAL QUALITY AUDIT"
        )
        print("=" * 100)

        print(
            f"Upcoming intelligence rows: "
            f"{len(rows)}"
        )

        print(
            f"Production eligible: "
            f"{len(eligible)}"
        )

        print(
            f"Average quality: "
            f"{avg_quality:.1f}"
        )

        print(
            f"Average uncertainty: "
            f"{avg_uncertainty:.1f}%"
        )

        print()

        for tier in [
            "A+",
            "A",
            "B",
            "C",
            "D",
        ]:

            print(
                f"{tier:<3}: "
                f"{tiers[tier]}"
            )

        print()

        top = sorted(
            rows,
            key=lambda row:
                row.quality_score,
            reverse=True,
        )[:10]

        print(
            "TOP QUALITY SIGNALS"
        )

        for row in top:

            print(
                f"Signal {row.signal_id:<4} "
                f"quality="
                f"{row.quality_score:>5.1f} "
                f"tier="
                f"{row.quality_tier:<2} "
                f"uncertainty="
                f"{row.uncertainty:>5.1f}% "
                f"eligible="
                f"{bool(row.production_eligible)}"
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