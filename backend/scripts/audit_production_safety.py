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
    is_match_production_ready,
)


MIN_EDGE = 5.0


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
            "ANALITIKO PRODUCTION SAFETY AUDIT"
        )
        print("=" * 100)

        # ====================================================
        # VALUE SIGNALS
        # ====================================================

        value_signals = (
            db.query(Signal)
            .filter(
                Signal.is_value.is_(True)
            )
            .all()
        )

        broken_value = 0

        for signal in value_signals:

            if (
                signal.odds is None
                or
                signal.edge is None
                or
                signal.expected_value
                is None
                or
                float(signal.odds) <= 1.0
                or
                float(signal.edge) < MIN_EDGE
                or
                float(
                    signal.expected_value
                ) <= 0.0
            ):

                broken_value += 1

        if broken_value:

            failures += 1

            print(
                f"[FAIL] Invalid VALUE signals: "
                f"{broken_value}"
            )

        else:

            print(
                "[OK] VALUE gate integrity"
            )

        # ====================================================
        # ACTIVE UPCOMING SIGNAL DATA QUALITY
        # ====================================================

        active = (
            db.query(Signal)
            .join(
                Match,
                Match.id
                == Signal.match_id,
            )
            .filter(
                Signal.active.is_(True),
                Match.match_date >= now,
            )
            .all()
        )

        bad_quality = 0

        for signal in active:

            match = (
                db.query(Match)
                .filter(
                    Match.id
                    == signal.match_id
                )
                .first()
            )

            if (
                match is not None
                and
                not is_match_production_ready(
                    db=db,
                    match=match,
                )
            ):

                bad_quality += 1

        if bad_quality:

            failures += 1

            print(
                f"[FAIL] Active signals "
                f"without READY data: "
                f"{bad_quality}"
            )

        else:

            print(
                "[OK] Active signal data gate"
            )

        # ====================================================
        # COMBINATIONS
        # ====================================================

        combinations = (
            db.query(Combination)
            .all()
        )

        invalid_combo_signal = 0
        correlated_matches = 0

        for combination in combinations:

            selections = (
                db.query(
                    CombinationSelection
                )
                .filter(
                    CombinationSelection
                    .combination_id
                    == combination.id
                )
                .all()
            )

            seen_matches = set()

            for selection in selections:

                if (
                    selection.match_id
                    in seen_matches
                ):

                    correlated_matches += 1

                seen_matches.add(
                    selection.match_id
                )

                signal = (
                    db.query(Signal)
                    .filter(
                        Signal.id
                        == selection.signal_id
                    )
                    .first()
                )

                if (
                    signal is None
                    or
                    not signal.is_value
                ):

                    invalid_combo_signal += 1

        if invalid_combo_signal:

            failures += 1

            print(
                f"[FAIL] Combination selections "
                f"without VALUE signal: "
                f"{invalid_combo_signal}"
            )

        else:

            print(
                "[OK] Combination VALUE gate"
            )

        if correlated_matches:

            failures += 1

            print(
                f"[FAIL] Multiple selections "
                f"from same match: "
                f"{correlated_matches}"
            )

        else:

            print(
                "[OK] Max one selection per match"
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
                f"({failures} checks)"
            )

        print("=" * 100)

    finally:

        db.close()


if __name__ == "__main__":
    run()