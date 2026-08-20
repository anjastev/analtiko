import hashlib

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

from app.services.market_policy import (
    market_allows_combinations,
)

from app.services.match_data_quality import (
    is_match_production_ready,
)


SPORT = "football"


ALL_MARKETS = {
    "DC",
    "OU_25",
    "BTTS",
}


MARKETS = {
    code
    for code in ALL_MARKETS
    if market_allows_combinations(
        code
    )
}


STRATEGIES = [
    "SAFE",
    "BALANCED",
    "AGGRESSIVE",
]


def build_signature(
    strategy: str,
    selected,
):

    parts = []

    for item in sorted(
        selected,
        key=lambda value: (
            value.match_id,
            value.market_code,
            value.selection,
        ),
    ):

        parts.append(
            f"{item.match_id}:"
            f"{item.market_code}:"
            f"{item.selection}"
        )

    raw = (
        strategy
        + "|"
        + "|".join(
            parts
        )
    )

    return hashlib.sha256(
        raw.encode(
            "utf-8"
        )
    ).hexdigest()


def estimate_probability(
    selected,
):

    probability = 1.0

    for item in selected:

        probability *= (
            item.probability
            / 100.0
        )

    return round(
        probability
        * 100.0,
        4,
    )


def run():

    db = SessionLocal()

    now = datetime.now(
        timezone.utc
    )

    try:

        markets = (
            db.query(Market)
            .filter(
                Market.sport
                == SPORT,

                Market.code.in_(
                    MARKETS
                ),
            )
            .all()
        )

        market_map = {
            market.id:
                market
            for market in markets
        }

        signals = (
            db.query(Signal)
            .join(
                Match,
                Match.id
                == Signal.match_id,
            )
            .filter(
                Signal.market_id.in_(
                    list(
                        market_map.keys()
                    )
                ),

                Signal.active.is_(True),

                Match.match_date
                >= now,
            )
            .all()
        )

        candidates = []

        data_blocked = 0
        match_cache = {}
        quality_cache = {}

        for signal in signals:

            match = (
                match_cache.get(
                    signal.match_id
                )
            )

            if match is None:

                match = (
                    db.query(Match)
                    .filter(
                        Match.id
                        == signal.match_id
                    )
                    .first()
                )

                match_cache[
                    signal.match_id
                ] = match

            if match is None:
                continue

            if (
                signal.match_id
                not in quality_cache
            ):

                quality_cache[
                    signal.match_id
                ] = (
                    is_match_production_ready(
                        db=db,
                        match=match,
                    )
                )

            if not (
                quality_cache[
                    signal.match_id
                ]
            ):

                data_blocked += 1
                continue

            market = (
                market_map[
                    signal.market_id
                ]
            )

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

            # ============================================================
            # PRODUCTION VALUE / ODDS GATE
            # ============================================================

            if signal.odds is None:
                continue

            if signal.edge is None:
                continue

            if float(signal.edge) < 5.0:
                continue

            if float(signal.odds) <= 1.0:
                continue

            if not signal.is_value:
                continue

            if signal.odds is None:
                continue

            if signal.edge is None:
                continue

            if signal.expected_value is None:
                continue

            if float(signal.edge) < 5.0:
                continue

            if float(signal.expected_value) <= 0.0:
                continue

            if float(signal.odds) <= 1.0:
                continue




            candidates.append(
                CombinationCandidate(
                    signal_id=(
                        signal.id
                    ),

                    match_id=(
                        signal.match_id
                    ),

                    market_code=(
                        market.code
                    ),

                    selection=(
                        signal.selection
                    ),

                    signal_type=(
                        signal.signal_type
                    ),

                    probability=(
                        float(
                            signal.model_probability
                        )
                    ),

                    edge=(
                        signal.edge
                    ),

                    score=(
                        score
                    ),
                )
            )

        print()
        print("=" * 100)
        print(
            "ANALITIKO PRODUCTION COMBINATION ENGINE"
        )
        print("=" * 100)

        print(
            f"Active allowed signals: "
            f"{len(signals)}"
        )

        print(
            f"Production candidates: "
            f"{len(candidates)}"
        )

        print(
            f"Data blocked: "
            f"{data_blocked}"
        )

        created = 0
        unchanged = 0

        for strategy in STRATEGIES:

            selected = (
                select_candidates(
                    candidates=(
                        candidates
                    ),
                    strategy=(
                        strategy
                    ),
                )
            )

            print()
            print("-" * 100)

            print(
                f"STRATEGY: "
                f"{strategy}"
            )

            if not selected:

                print(
                    "No eligible selections."
                )

                continue

            signature = (
                build_signature(
                    strategy=(
                        strategy
                    ),
                    selected=(
                        selected
                    ),
                )
            )

            existing = (
                db.query(
                    Combination
                )
                .filter(
                    Combination.signature
                    == signature
                )
                .first()
            )

            if existing:

                unchanged += 1

                print(
                    f"UNCHANGED: "
                    f"{existing.id}"
                )

                continue

            # =================================================
            # DIRECT ODDS
            # =================================================

            odds_map = {}
            odds_values = []

            for item in selected:

                odds_row = (
                    get_best_market_odds(
                        db=db,
                        match_id=(
                            item.match_id
                        ),
                        market_code=(
                            item.market_code
                        ),
                        selection=(
                            item.selection
                        ),
                        sport=SPORT,
                    )
                )

                odds_map[
                    item.signal_id
                ] = odds_row

                odds_values.append(
                    float(
                        odds_row.odds
                    )
                    if odds_row
                    else None
                )

            total_odds = None

            if (
                odds_values
                and
                all(
                    value is not None
                    for value
                    in odds_values
                )
            ):

                total_odds = 1.0

                for value in odds_values:

                    total_odds *= value

                total_odds = round(
                    total_odds,
                    4,
                )

            estimated_probability = (
                estimate_probability(
                    selected
                )
            )

            probabilities = [
                item.probability
                for item in selected
            ]

            risk_score = round(
                100.0
                -
                (
                    sum(
                        probabilities
                    )
                    /
                    len(
                        probabilities
                    )
                ),
                4,
            )

            combination = (
                Combination(
                    name=(
                        f"Analitiko "
                        f"{strategy.title()} "
                        f"Production"
                    ),

                    strategy=(
                        strategy
                    ),

                    sport=SPORT,

                    total_odds=(
                        total_odds
                    ),

                    estimated_probability=(
                        estimated_probability
                    ),

                    risk_score=(
                        risk_score
                    ),

                    status="pending",

                    signature=(
                        signature
                    ),
                )
            )

            db.add(
                combination
            )

            db.flush()

            for item in selected:

                odds_row = (
                    odds_map[
                        item.signal_id
                    ]
                )

                db.add(
                    CombinationSelection(
                        combination_id=(
                            combination.id
                        ),

                        signal_id=(
                            signal.id
                        ),

                        match_id=(
                            signal.match_id
                        ),

                        selection=(
                            f"{market.code}:"
                            f"{signal.selection}"
                        ),

                        odds=(
                            signal.odds
                        ),

                        probability=(
                            signal.model_probability
                        ),

                        correlation_group=(
                            f"match:"
                            f"{signal.match_id}"
                        ),
                    )
                )

                match = (
                    match_cache[
                        item.match_id
                    ]
                )

                print(
                    f"  {match.home_team.name} "
                    f"vs "
                    f"{match.away_team.name}"
                )

                print(
                    f"    "
                    f"{item.market_code} "
                    f"{item.selection} "
                    f"{item.probability:.1f}%"
                )

            print(
                f"Created combination: "
                f"{combination.id}"
            )

            print(
                f"Estimated probability: "
                f"{estimated_probability:.2f}%"
            )

            print(
                "Total odds: "
                + (
                    f"{total_odds:.2f}"
                    if total_odds
                    is not None
                    else "N/A"
                )
            )

            created += 1

        db.commit()

        print()
        print("=" * 100)
        print(
            "PRODUCTION COMBINATION SUMMARY"
        )
        print("=" * 100)

        print(
            f"Created: "
            f"{created}"
        )

        print(
            f"Unchanged: "
            f"{unchanged}"
        )

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