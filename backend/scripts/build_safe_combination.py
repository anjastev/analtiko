from datetime import (
    datetime,
    timezone,
)

from app.database.database import (
    Base,
    SessionLocal,
    engine,
)

from app.models.combination import Combination
from app.models.combination_selection import (
    CombinationSelection,
)
from app.models.market import Market
from app.models.match import Match
from app.models.signal import Signal

from app.services.combination_engine import (
    CombinationCandidate,
    calculate_candidate_score,
    select_safe_candidates,
)

import app.models


# ============================================================
# CONFIG
# ============================================================

SPORT = "football"
MARKET_CODE = "DC"

NUMBER_OF_SELECTIONS = 3

ALLOWED_SIGNAL_TYPES = {
    "STRONG",
    "ELITE",
    "ULTRA",
}


# ============================================================
# HELPERS
# ============================================================

def get_market(
    db,
):
    return (
        db.query(Market)
        .filter(
            Market.sport == SPORT,
            Market.code == MARKET_CODE,
        )
        .first()
    )


def estimate_combination_probability(
    selections,
):
    """
    First simple version.

    Assumes selections are independent.

    Because we enforce one selection per match, this is much
    safer than combining several correlated selections from the
    same match.

    Still treat this as an estimate, not a guarantee.
    """

    probability = 1.0

    for selection in selections:

        probability *= (
            selection.probability
            / 100.0
        )

    return round(
        probability * 100.0,
        4,
    )


# ============================================================
# MAIN
# ============================================================

def run():

    Base.metadata.create_all(
        bind=engine
    )

    db = SessionLocal()

    now = datetime.now(
        timezone.utc
    )

    try:

        market = (
            get_market(
                db
            )
        )

        if market is None:

            raise RuntimeError(
                "Double Chance market not found."
            )

        signals = (
            db.query(Signal)
            .join(
                Match,
                Match.id == Signal.match_id,
            )
            .filter(
                Signal.market_id == market.id,
                Signal.active.is_(True),
                Signal.signal_type.in_(
                    ALLOWED_SIGNAL_TYPES
                ),
                Match.match_date >= now,
            )
            .order_by(
                Signal.confidence_score.desc()
            )
            .all()
        )

        print()
        print("=" * 80)
        print(
            "ANALITIKO SAFE COMBINATION ENGINE"
        )
        print("=" * 80)

        print(
            f"Active candidate signals: "
            f"{len(signals)}"
        )

        candidates = []

        for signal in signals:

            score = (
                calculate_candidate_score(
                    probability=(
                        signal.model_probability
                    ),
                    signal_type=(
                        signal.signal_type
                    ),
                    edge=signal.edge,
                )
            )

            candidate = (
                CombinationCandidate(
                    signal_id=signal.id,
                    match_id=signal.match_id,
                    selection=signal.selection,
                    signal_type=signal.signal_type,
                    probability=(
                        signal.model_probability
                    ),
                    edge=signal.edge,
                    score=score,
                )
            )

            candidates.append(
                candidate
            )

        selected = (
            select_safe_candidates(
                candidates=candidates,
                number_of_selections=(
                    NUMBER_OF_SELECTIONS
                ),
            )
        )

        if not selected:

            print()
            print(
                "No combination could be built."
            )

            print("=" * 80)
            return

        estimated_probability = (
            estimate_combination_probability(
                selected
            )
        )

        average_probability = (
            sum(
                item.probability
                for item in selected
            )
            / len(selected)
        )

        combination = Combination(
            name="Analitiko Safe Combination",
            strategy="SAFE",
            sport=SPORT,
            total_odds=None,
            estimated_probability=(
                estimated_probability
            ),
            risk_score=round(
                100.0
                - average_probability,
                4,
            ),
            status="pending",
        )

        db.add(
            combination
        )

        db.flush()

        print()

        print(
            f"Selected: "
            f"{len(selected)}"
        )

        print()

        for index, candidate in enumerate(
            selected,
            start=1,
        ):

            signal = (
                db.query(Signal)
                .filter(
                    Signal.id
                    == candidate.signal_id
                )
                .first()
            )

            match = (
                db.query(Match)
                .filter(
                    Match.id
                    == candidate.match_id
                )
                .first()
            )

            if (
                signal is None
                or match is None
            ):
                continue

            row = CombinationSelection(
                combination_id=(
                    combination.id
                ),
                signal_id=signal.id,
                match_id=match.id,
                selection=(
                    candidate.selection
                ),
                odds=None,
                probability=(
                    candidate.probability
                ),
                correlation_group=(
                    f"match:{match.id}"
                ),
            )

            db.add(
                row
            )

            print("-" * 80)

            print(
                f"{index}. "
                f"{match.home_team.name} "
                f"vs "
                f"{match.away_team.name}"
            )

            print(
                f"Selection: "
                f"{candidate.selection}"
            )

            print(
                f"Signal: "
                f"{candidate.signal_type}"
            )

            print(
                f"Probability: "
                f"{candidate.probability:.1f}%"
            )

            if (
                candidate.edge
                is not None
            ):

                print(
                    f"Edge: "
                    f"{candidate.edge:+.1f}%"
                )

            else:

                print(
                    "Edge: N/A"
                )

            print(
                f"Candidate score: "
                f"{candidate.score:.1f}"
            )

        db.commit()

        print()
        print("=" * 80)

        print(
            f"Combination ID: "
            f"{combination.id}"
        )

        print(
            f"Strategy: SAFE"
        )

        print(
            f"Estimated combined "
            f"probability: "
            f"{estimated_probability:.2f}%"
        )

        print(
            f"Risk score: "
            f"{combination.risk_score:.2f}"
        )

        print()

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