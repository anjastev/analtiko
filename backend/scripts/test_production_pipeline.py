from datetime import (
    datetime,
    timezone,
)

from app.database.database import (
    SessionLocal,
)

from app.models.combination import (
    Combination,
)

from app.models.combination_selection import (
    CombinationSelection,
)

from app.models.match import Match
from app.models.signal import Signal

from app.services.match_data_quality import (
    evaluate_match_data_quality,
)


def run():

    db = SessionLocal()

    now = datetime.now(
        timezone.utc
    )

    failures = 0

    try:

        print()
        print("=" * 100)
        print(
            "ANALITIKO PRODUCTION PIPELINE TEST"
        )
        print("=" * 100)

        # ====================================================
        # ACTIVE SIGNALS
        # ====================================================

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

        print(
            f"Upcoming active signals: "
            f"{len(signals)}"
        )

        bad_signals = 0

        for signal in signals:

            match = (
                db.query(Match)
                .filter(
                    Match.id
                    == signal.match_id
                )
                .first()
            )

            quality = (
                evaluate_match_data_quality(
                    db=db,
                    match=match,
                )
            )

            if not quality["ready"]:

                bad_signals += 1

                print(
                    f"[FAIL] Signal "
                    f"{signal.id} "
                    f"match={signal.match_id} "
                    f"quality="
                    f"{quality['status']}"
                )

        if bad_signals == 0:

            print(
                "[OK] All active upcoming "
                "signals are production-ready"
            )

        else:

            failures += 1

        # ====================================================
        # SIGNATURES
        # ====================================================

        signed = (
            db.query(Combination)
            .filter(
                Combination.signature
                .isnot(None)
            )
            .all()
        )

        signatures = {}

        duplicates = 0

        for combo in signed:

            if (
                combo.signature
                in signatures
            ):

                duplicates += 1

            signatures[
                combo.signature
            ] = combo.id

        if duplicates == 0:

            print(
                "[OK] Duplicate "
                "combination signatures: 0"
            )

        else:

            failures += 1

            print(
                f"[FAIL] Duplicate "
                f"combination signatures: "
                f"{duplicates}"
            )

        # ====================================================
        # CURRENT DATA COVERAGE
        # ====================================================

        matches = (
            db.query(Match)
            .filter(
                Match.match_date
                >= now
            )
            .all()
        )

        ready_matches = 0

        for match in matches:

            quality = (
                evaluate_match_data_quality(
                    db=db,
                    match=match,
                )
            )

            if quality["ready"]:
                ready_matches += 1

        print(
            f"[INFO] Future READY matches: "
            f"{ready_matches}/"
            f"{len(matches)}"
        )

        print()
        print("=" * 100)

        if failures == 0:

            print(
                "STATUS: OK"
            )

        else:

            print(
                f"STATUS: PARTIAL "
                f"({failures} failures)"
            )

        print("=" * 100)

    finally:

        db.close()


if __name__ == "__main__":
    run()