from sqlalchemy import (
    func,
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
from app.models.market_odds import (
    MarketOdds,
)
from app.models.match import Match
from app.models.signal import Signal
from app.models.team_match_history import (
    TeamMatchHistory,
)


def run():

    db = SessionLocal()

    failures = 0

    try:

        print()
        print("=" * 100)
        print(
            "ANALITIKO DATABASE INTEGRITY AUDIT"
        )
        print("=" * 100)

        # ====================================================
        # HISTORY DUPLICATES
        # ====================================================

        history_duplicates = (
            db.query(
                TeamMatchHistory.team_id,
                TeamMatchHistory.fixture_external_id,
                func.count(
                    TeamMatchHistory.id
                ),
            )
            .group_by(
                TeamMatchHistory.team_id,
                TeamMatchHistory.fixture_external_id,
            )
            .having(
                func.count(
                    TeamMatchHistory.id
                ) > 1
            )
            .count()
        )

        if history_duplicates:

            failures += 1

            print(
                f"[FAIL] History duplicates: "
                f"{history_duplicates}"
            )

        else:

            print(
                "[OK] History duplicates: 0"
            )

        # ====================================================
        # COMBINATION SIGNATURE DUPLICATES
        # ====================================================

        combo_duplicates = (
            db.query(
                Combination.signature,
                func.count(
                    Combination.id
                ),
            )
            .filter(
                Combination.signature
                .isnot(None)
            )
            .group_by(
                Combination.signature
            )
            .having(
                func.count(
                    Combination.id
                ) > 1
            )
            .count()
        )

        if combo_duplicates:

            failures += 1

            print(
                f"[FAIL] Combination "
                f"signature duplicates: "
                f"{combo_duplicates}"
            )

        else:

            print(
                "[OK] Combination "
                "signature duplicates: 0"
            )

        # ====================================================
        # SIGNAL REFERENCES
        # ====================================================

        signals = (
            db.query(Signal)
            .all()
        )

        bad_signal_refs = 0

        for signal in signals:

            match_exists = (
                db.query(Match.id)
                .filter(
                    Match.id
                    == signal.match_id
                )
                .first()
            )

            if match_exists is None:
                bad_signal_refs += 1

        if bad_signal_refs:

            failures += 1

            print(
                f"[FAIL] Signals with "
                f"missing match: "
                f"{bad_signal_refs}"
            )

        else:

            print(
                "[OK] Signal match references"
            )

        # ====================================================
        # VALUE INTEGRITY
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
                signal.bookmaker is None
                or
                signal.market_probability
                is None
                or
                signal.edge is None
                or
                signal.expected_value
                is None
            ):

                broken_value += 1

        if broken_value:

            failures += 1

            print(
                f"[FAIL] Incomplete VALUE "
                f"signals: "
                f"{broken_value}"
            )

        else:

            print(
                "[OK] VALUE signal integrity"
            )

        # ====================================================
        # COMBINATION SELECTION REFERENCES
        # ====================================================

        selections = (
            db.query(
                CombinationSelection
            )
            .all()
        )

        broken_selections = 0

        for selection in selections:

            signal = (
                db.query(Signal.id)
                .filter(
                    Signal.id
                    == selection.signal_id
                )
                .first()
            )

            match = (
                db.query(Match.id)
                .filter(
                    Match.id
                    == selection.match_id
                )
                .first()
            )

            if (
                signal is None
                or match is None
            ):

                broken_selections += 1

        if broken_selections:

            failures += 1

            print(
                f"[FAIL] Broken combination "
                f"selections: "
                f"{broken_selections}"
            )

        else:

            print(
                "[OK] Combination selection "
                "references"
            )

        # ====================================================
        # BASIC COUNTS
        # ====================================================

        print()
        print(
            f"[INFO] Matches: "
            f"{db.query(Match).count()}"
        )

        print(
            f"[INFO] History rows: "
            f"{db.query(TeamMatchHistory).count()}"
        )

        print(
            f"[INFO] Odds rows: "
            f"{db.query(MarketOdds).count()}"
        )

        print(
            f"[INFO] Signals: "
            f"{db.query(Signal).count()}"
        )

        print(
            f"[INFO] VALUE signals: "
            f"{len(value_signals)}"
        )

        print(
            f"[INFO] Combinations: "
            f"{db.query(Combination).count()}"
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