import hashlib

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
    select_candidates,
)

from app.services.market_odds_service import (
    get_best_market_odds,
)

import app.models


# ============================================================
# CONFIG
# ============================================================

SPORT = "football"

MARKET_CODE = "DC"


ALLOWED_SIGNAL_TYPES = {
    "STRONG",
    "ELITE",
    "ULTRA",
}


STRATEGIES_TO_BUILD = [
    "SAFE",
    "BALANCED",
    "AGGRESSIVE",
]


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

    probability = 1.0

    for item in selections:

        probability *= (
            item.probability
            / 100.0
        )

    return round(
        probability * 100.0,
        4,
    )


def calculate_risk_score(
    selections,
):

    if not selections:
        return None

    average_probability = (
        sum(
            item.probability
            for item in selections
        )
        / len(selections)
    )

    return round(
        100.0
        - average_probability,
        4,
    )


def build_signature(
    strategy: str,
    selected,
):

    parts = []

    for candidate in sorted(
        selected,
        key=lambda item: (
            item.match_id,
            item.selection,
        ),
    ):

        parts.append(
            f"{candidate.match_id}:"
            f"{candidate.selection}"
        )

    raw = (
        f"{strategy}|"
        + "|".join(parts)
    )

    return hashlib.sha256(
        raw.encode(
            "utf-8"
        )
    ).hexdigest()


def find_existing_combination(
    db,
    signature: str,
):

    return (
        db.query(Combination)
        .filter(
            Combination.signature
            == signature
        )
        .order_by(
            Combination.id.desc()
        )
        .first()
    )


def calculate_total_odds(
    selection_odds,
):

    if not selection_odds:
        return None

    if any(
        value is None
        for value in selection_odds
    ):
        return None

    total = 1.0

    for value in selection_odds:

        total *= float(
            value
        )

    return round(
        total,
        4,
    )


def create_combination(
    db,
    strategy: str,
    selected,
):

    if not selected:
        return None, False

    signature = (
        build_signature(
            strategy=strategy,
            selected=selected,
        )
    )

    existing = (
        find_existing_combination(
            db=db,
            signature=signature,
        )
    )

    if existing is not None:

        return (
            existing,
            False,
        )

    estimated_probability = (
        estimate_combination_probability(
            selected
        )
    )

    risk_score = (
        calculate_risk_score(
            selected
        )
    )

    # ========================================================
    # ODDS FOR EACH SELECTION
    # ========================================================

    selection_odds = []

    odds_rows = {}

    for candidate in selected:

        odds_row = (
            get_best_market_odds(
                db=db,
                match_id=(
                    candidate.match_id
                ),
                market_code=(
                    MARKET_CODE
                ),
                selection=(
                    candidate.selection
                ),
                sport=SPORT,
            )
        )

        odds_rows[
            candidate.signal_id
        ] = odds_row

        if odds_row is None:

            selection_odds.append(
                None
            )

        else:

            selection_odds.append(
                odds_row.odds
            )

    total_odds = (
        calculate_total_odds(
            selection_odds
        )
    )

    # ========================================================
    # COMBINATION
    # ========================================================

    combination = Combination(
        name=(
            f"Analitiko "
            f"{strategy.title()} "
            f"Combination"
        ),
        strategy=strategy,
        sport=SPORT,
        total_odds=total_odds,
        estimated_probability=(
            estimated_probability
        ),
        risk_score=risk_score,
        status="pending",
        signature=signature,
    )

    db.add(
        combination
    )

    db.flush()

    # ========================================================
    # SELECTIONS
    # ========================================================

    for candidate in selected:

        odds_row = (
            odds_rows.get(
                candidate.signal_id
            )
        )

        row = CombinationSelection(
            combination_id=(
                combination.id
            ),
            signal_id=(
                candidate.signal_id
            ),
            match_id=(
                candidate.match_id
            ),
            selection=(
                candidate.selection
            ),
            odds=(
                odds_row.odds
                if odds_row
                is not None
                else None
            ),
            probability=(
                candidate.probability
            ),
            correlation_group=(
                f"match:"
                f"{candidate.match_id}"
            ),
        )

        db.add(
            row
        )

    return (
        combination,
        True,
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
                "Double Chance market "
                "not found."
            )

        # ====================================================
        # LOAD SIGNALS
        # ====================================================

        signals = (
            db.query(Signal)
            .join(
                Match,
                Match.id
                == Signal.match_id,
            )
            .filter(
                Signal.market_id
                == market.id,

                Signal.active
                .is_(True),

                Signal.signal_type
                .in_(
                    ALLOWED_SIGNAL_TYPES
                ),

                Match.match_date
                >= now,
            )
            .order_by(
                Signal.confidence_score
                .desc()
            )
            .all()
        )

        print()
        print("=" * 80)
        print(
            "ANALITIKO COMBINATION ENGINE V2"
        )
        print("=" * 80)

        print(
            f"Active signals: "
            f"{len(signals)}"
        )

        # ====================================================
        # CANDIDATES
        # ====================================================

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

            candidates.append(
                CombinationCandidate(
                    signal_id=signal.id,
                    match_id=(
                        signal.match_id
                    ),
                    selection=(
                        signal.selection
                    ),
                    signal_type=(
                        signal.signal_type
                    ),
                    probability=(
                        signal.model_probability
                    ),
                    edge=signal.edge,
                    score=score,
                )
            )

        created_count = 0
        unchanged_count = 0

        # ====================================================
        # STRATEGIES
        # ====================================================

        for strategy in (
            STRATEGIES_TO_BUILD
        ):

            print()
            print("=" * 80)
            print(
                f"STRATEGY: "
                f"{strategy}"
            )
            print("=" * 80)

            selected = (
                select_candidates(
                    candidates=(
                        candidates
                    ),
                    strategy=strategy,
                )
            )

            if not selected:

                print(
                    "No qualifying "
                    "selections."
                )

                continue

            combination, created = (
                create_combination(
                    db=db,
                    strategy=strategy,
                    selected=selected,
                )
            )

            for index, candidate in enumerate(
                selected,
                start=1,
            ):

                match = (
                    db.query(Match)
                    .filter(
                        Match.id
                        == candidate.match_id
                    )
                    .first()
                )

                if match is None:
                    continue

                odds_row = (
                    get_best_market_odds(
                        db=db,
                        match_id=match.id,
                        market_code=(
                            MARKET_CODE
                        ),
                        selection=(
                            candidate.selection
                        ),
                        sport=SPORT,
                    )
                )

                print()

                print(
                    f"{index}. "
                    f"{match.home_team.name} "
                    f"vs "
                    f"{match.away_team.name}"
                )

                print(
                    f"   Selection: "
                    f"{candidate.selection}"
                )

                print(
                    f"   Signal: "
                    f"{candidate.signal_type}"
                )

                print(
                    f"   Probability: "
                    f"{candidate.probability:.1f}%"
                )

                if (
                    candidate.edge
                    is not None
                ):

                    print(
                        f"   Edge: "
                        f"{candidate.edge:+.1f}%"
                    )

                else:

                    print(
                        "   Edge: N/A"
                    )

                if odds_row is not None:

                    print(
                        f"   Odds: "
                        f"{odds_row.odds:.2f}"
                    )

                    print(
                        f"   Bookmaker: "
                        f"{odds_row.bookmaker}"
                    )

                else:

                    print(
                        "   Odds: N/A"
                    )

                print(
                    f"   Score: "
                    f"{candidate.score:.1f}"
                )

            print()

            if created:

                created_count += 1

                print(
                    f"Combination CREATED: "
                    f"{combination.id}"
                )

            else:

                unchanged_count += 1

                print(
                    f"Combination UNCHANGED: "
                    f"{combination.id}"
                )

            print(
                "Estimated probability: "
                f"{combination.estimated_probability:.2f}%"
            )

            if (
                combination.total_odds
                is not None
            ):

                print(
                    f"Total odds: "
                    f"{combination.total_odds:.2f}"
                )

            else:

                print(
                    "Total odds: N/A"
                )

            print(
                f"Risk score: "
                f"{combination.risk_score:.2f}"
            )

        # ====================================================
        # COMMIT
        # ====================================================

        db.commit()

        print()
        print("=" * 80)
        print(
            "COMBINATION SUMMARY"
        )
        print("=" * 80)

        print(
            f"Created: "
            f"{created_count}"
        )

        print(
            f"Unchanged: "
            f"{unchanged_count}"
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