from app.database.database import (
    SessionLocal,
)

from app.models.league_reliability import (
    LeagueReliability,
)

from app.models.signal_intelligence import (
    SignalIntelligence,
)


def run():

    db = SessionLocal()

    failures = 0

    try:

        print()
        print("=" * 100)
        print(
            "ANALITIKO INTELLIGENCE BATCH 2 TEST"
        )
        print("=" * 100)

        league_count = (
            db.query(
                LeagueReliability
            )
            .count()
        )

        intelligence_count = (
            db.query(
                SignalIntelligence
            )
            .count()
        )

        if league_count > 0:

            print(
                f"[OK] League reliability: "
                f"{league_count}"
            )

        else:

            failures += 1

            print(
                "[FAIL] League reliability"
            )

        if intelligence_count > 0:

            print(
                f"[OK] Signal intelligence: "
                f"{intelligence_count}"
            )

        else:

            failures += 1

            print(
                "[FAIL] Signal intelligence"
            )

        invalid_quality = (
            db.query(
                SignalIntelligence
            )
            .filter(
                (
                    SignalIntelligence
                    .quality_score
                    < 0
                )
                |
                (
                    SignalIntelligence
                    .quality_score
                    > 100
                )
            )
            .count()
        )

        if invalid_quality == 0:

            print(
                "[OK] Quality bounds"
            )

        else:

            failures += 1

            print(
                f"[FAIL] Invalid quality: "
                f"{invalid_quality}"
            )

        invalid_uncertainty = (
            db.query(
                SignalIntelligence
            )
            .filter(
                (
                    SignalIntelligence
                    .uncertainty
                    < 0
                )
                |
                (
                    SignalIntelligence
                    .uncertainty
                    > 100
                )
            )
            .count()
        )

        if invalid_uncertainty == 0:

            print(
                "[OK] Uncertainty bounds"
            )

        else:

            failures += 1

            print(
                f"[FAIL] Invalid uncertainty: "
                f"{invalid_uncertainty}"
            )

        print()
        print("=" * 100)

        if failures == 0:

            print(
                "STATUS: OK"
            )

        else:

            print(
                f"STATUS: FAILED "
                f"({failures})"
            )

        print("=" * 100)

        if failures:
            raise SystemExit(1)

    finally:

        db.close()


if __name__ == "__main__":
    run()