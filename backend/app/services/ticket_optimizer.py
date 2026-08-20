from __future__ import annotations

from itertools import combinations
from math import prod

from sqlalchemy.orm import Session

from app.models.match import Match
from app.models.market import Market
from app.models.signal import Signal
from app.models.signal_intelligence import (
    SignalIntelligence,
)


STRATEGY_POLICIES = {

    "SAFE": {
        "min_quality": 75.0,
        "allowed_tiers": {
            "A+",
            "A",
            "B",
        },
        "max_uncertainty": 38.0,
        "min_probability": 72.0,
        "min_edge": 5.0,
        "min_ev": 0.0,
        "min_selections": 2,
        "default_selections": 2,
        "max_selections": 3,
        "default_target_odds": 2.00,
        "max_same_league": 2,
"max_anomaly_score": 25.0,
"allow_review": False,
    },

    "BALANCED": {
        "min_quality": 68.0,
        "allowed_tiers": {
            "A+",
            "A",
            "B",
            "C",
        },
        "max_uncertainty": 43.0,
        "min_probability": 67.0,
        "min_edge": 5.0,
        "min_ev": 0.0,
        "min_selections": 2,
        "default_selections": 3,
        "max_selections": 4,
        "default_target_odds": 2.75,
        "max_same_league": 2,
"max_anomaly_score": 40.0,
"allow_review": False,
    },

    "AGGRESSIVE": {
        "min_quality": 60.0,
        "allowed_tiers": {
            "A+",
            "A",
            "B",
            "C",
        },
        "max_uncertainty": 48.0,
        "min_probability": 60.0,
        "min_edge": 5.0,
        "min_ev": 0.0,
        "min_selections": 2,
        "default_selections": 4,
        "max_selections": 5,
        "default_target_odds": 4.00,
        "max_same_league": 3,
"max_anomaly_score": 55.0,
"allow_review": True,
    },
}


def clamp(
    value: float,
    low: float,
    high: float,
) -> float:

    return max(
        low,
        min(
            high,
            value,
        ),
    )


def latest_intelligence(
    db: Session,
    signal_id: int,
):

    return (
        db.query(
            SignalIntelligence
        )
        .filter(
            SignalIntelligence.signal_id
            == signal_id
        )
        .order_by(
            SignalIntelligence
            .calculated_at
            .desc(),

            SignalIntelligence.id
            .desc(),
        )
        .first()
    )


def candidate_score(
    *,
    signal: Signal,
    intelligence: SignalIntelligence,
    strategy: str,
) -> float:

    quality = float(
        intelligence.quality_score
    )

    calibrated_probability = float(
        intelligence.calibrated_probability
    )

    uncertainty = float(
        intelligence.uncertainty
    )

    edge = float(
        signal.edge
        or 0.0
    )

    ev = float(
        signal.expected_value
        or 0.0
    )

    if strategy == "SAFE":

        score = (
            quality * 0.40
            + calibrated_probability * 0.35
            + edge * 0.10
            + min(ev, 25.0) * 0.05
            + (
                100.0
                - uncertainty
            ) * 0.10
        )

    elif strategy == "AGGRESSIVE":

        score = (
            quality * 0.25
            + calibrated_probability * 0.20
            + edge * 0.25
            + min(ev, 40.0) * 0.20
            + (
                100.0
                - uncertainty
            ) * 0.10
        )

    else:

        score = (
            quality * 0.35
            + calibrated_probability * 0.25
            + edge * 0.18
            + min(ev, 30.0) * 0.12
            + (
                100.0
                - uncertainty
            ) * 0.10
        )

    return round(
        score,
        6,
    )


def build_candidate_pool(
    db: Session,
    *,
    strategy: str,
    date_from,
    date_to,
    leagues: list[str] | None = None,
    exclude_leagues: list[str] | None = None,
    min_probability: float | None = None,
):

    strategy = (
        strategy
        .strip()
        .upper()
    )

    if strategy not in STRATEGY_POLICIES:

        strategy = "BALANCED"

    policy = (
        STRATEGY_POLICIES[
            strategy
        ]
    )

    requested_leagues = {
        value.strip().lower()
        for value in (
            leagues
            or []
        )
    }

    excluded_leagues = {
        value.strip().lower()
        for value in (
            exclude_leagues
            or []
        )
    }

    probability_floor = max(
        float(
            policy[
                "min_probability"
            ]
        ),
        float(
            min_probability
        )
        if min_probability
        is not None
        else 0.0,
    )

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
            Signal.odds.isnot(None),
            Signal.edge.isnot(None),
            Signal.expected_value.isnot(None),

            Match.match_date
            >= date_from,

            Match.match_date
            < date_to,
        )
        .all()
    )

    markets = {
        market.id:
            market.code
        for market in (
            db.query(Market)
            .all()
        )
    }

    pool = []

    for signal in signals:

        intelligence = (
            latest_intelligence(
                db,
                signal.id,
            )
        )

        if intelligence is None:
            continue

        if not bool(
            intelligence.production_eligible
        ):
            continue

        if (
            intelligence.quality_tier
            not in policy[
                "allowed_tiers"
            ]
        ):
            continue

        if (
            float(
                intelligence.quality_score
            )
            <
            float(
                policy[
                    "min_quality"
                ]
            )
        ):
            continue

        if (
            float(
                intelligence.uncertainty
            )
            >
            float(
                policy[
                    "max_uncertainty"
                ]
            )
        ):
            continue

        if (
                float(
                        intelligence.anomaly_score
                    )
                    >
                    float(
                        policy[
                            "max_anomaly_score"
                        ]
                    )
            ):
                continue

        if (
            float(
                intelligence.calibrated_probability
            )
            < probability_floor
        ):
            continue

        if (
            float(
                signal.edge
                or 0.0
            )
            <
            float(
                policy[
                    "min_edge"
                ]
            )
        ):
            continue

        if (
                    bool(
                        intelligence.requires_review
                    )
                    and
                    not policy[
                        "allow_review"
                    ]
            ):
                continue

        if (
            float(
                signal.expected_value
                or 0.0
            )
            <=
            float(
                policy[
                    "min_ev"
                ]
            )
        ):
            continue

        if (
            float(
                signal.odds
                or 0.0
            )
            <= 1.0
        ):
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

        league_name = (
            match.league.name
            if match.league
            else "Unknown"
        )

        league_key = (
            league_name
            .strip()
            .lower()
        )

        if (
            requested_leagues
            and
            league_key
            not in requested_leagues
        ):
            continue

        if (
            league_key
            in excluded_leagues
        ):
            continue

        pool.append(
            {
                "signal":
                    signal,

                "intelligence":
                    intelligence,

                "match":
                    match,

                "league":
                    league_name,

                "market":
                    markets.get(
                        signal.market_id,
                        "UNKNOWN",
                    ),

                "score":
                    candidate_score(
                        signal=signal,
                        intelligence=(
                            intelligence
                        ),
                        strategy=strategy,
                    ),
            }
        )

    pool.sort(
        key=lambda item:
            item[
                "score"
            ],
        reverse=True,
    )

    return pool


def combo_is_valid(
    combo: tuple,
    *,
    max_same_league: int,
) -> bool:

    seen_matches = set()

    league_counts = {}

    for item in combo:

        match_id = (
            item[
                "match"
            ].id
        )

        if match_id in seen_matches:
            return False

        seen_matches.add(
            match_id
        )

        league = (
            item[
                "league"
            ]
        )

        league_counts[
            league
        ] = (
            league_counts.get(
                league,
                0,
            )
            + 1
        )

        if (
            league_counts[
                league
            ]
            > max_same_league
        ):
            return False

    return True


def correlation_penalty(
    combo: tuple,
) -> float:

    penalty = 0.0

    leagues = [
        item[
            "league"
        ]
        for item in combo
    ]

    markets = [
        item[
            "market"
        ]
        for item in combo
    ]

    # Same-league concentration.
    for league in set(
        leagues
    ):

        count = (
            leagues.count(
                league
            )
        )

        if count > 1:

            penalty += (
                count - 1
            ) * 3.0

    # Current production is mostly DC,
    # so this is intentionally conservative.
    #
    # Later when OU/BTTS become ACTIVE,
    # pairwise market correlations should
    # replace this simple penalty.

    if (
        len(
            set(
                markets
            )
        )
        == 1
        and
        len(markets) >= 4
    ):

        penalty += 2.0

    return penalty


def combo_metrics(
    combo: tuple,
):

    total_odds = prod(
        float(
            item[
                "signal"
            ].odds
        )
        for item in combo
    )

    naive_probability = prod(
        float(
            item[
                "intelligence"
            ].calibrated_probability
        )
        / 100.0
        for item in combo
    )

    penalty = (
        correlation_penalty(
            combo
        )
    )

    conservative_probability = (
        naive_probability
        *
        (
            1.0
            -
            min(
                penalty,
                30.0,
            )
            / 100.0
        )
    )

    average_quality = (
        sum(
            float(
                item[
                    "intelligence"
                ].quality_score
            )
            for item in combo
        )
        / len(combo)
    )

    average_uncertainty = (
        sum(
            float(
                item[
                    "intelligence"
                ].uncertainty
            )
            for item in combo
        )
        / len(combo)
    )

    average_edge = (
        sum(
            float(
                item[
                    "signal"
                ].edge
                or 0.0
            )
            for item in combo
        )
        / len(combo)
    )

    average_ev = (
        sum(
            float(
                item[
                    "signal"
                ].expected_value
                or 0.0
            )
            for item in combo
        )
        / len(combo)
    )

    return {
        "total_odds":
            total_odds,

        "naive_probability":
            naive_probability
            * 100.0,

        "estimated_probability":
            conservative_probability
            * 100.0,

        "correlation_penalty":
            penalty,

        "average_quality":
            average_quality,

        "average_uncertainty":
            average_uncertainty,

        "average_edge":
            average_edge,

        "average_ev":
            average_ev,
    }


def combo_score(
    *,
    metrics: dict,
    strategy: str,
    target_odds: float,
):

    odds_distance = abs(
        metrics[
            "total_odds"
        ]
        - target_odds
    )

    odds_score = max(
        0.0,
        25.0
        - odds_distance
        * 10.0,
    )

    if strategy == "SAFE":

        score = (
            metrics[
                "estimated_probability"
            ]
            * 0.40
            +
            metrics[
                "average_quality"
            ]
            * 0.30
            +
            (
                100.0
                - metrics[
                    "average_uncertainty"
                ]
            )
            * 0.15
            +
            odds_score
            * 0.15
            -
            metrics[
                "correlation_penalty"
            ]
        )

    elif strategy == "AGGRESSIVE":

        score = (
            metrics[
                "estimated_probability"
            ]
            * 0.20
            +
            metrics[
                "average_quality"
            ]
            * 0.20
            +
            metrics[
                "average_edge"
            ]
            * 0.20
            +
            min(
                metrics[
                    "average_ev"
                ],
                30.0,
            )
            * 0.15
            +
            odds_score
            * 0.25
            -
            metrics[
                "correlation_penalty"
            ]
        )

    else:

        score = (
            metrics[
                "estimated_probability"
            ]
            * 0.30
            +
            metrics[
                "average_quality"
            ]
            * 0.25
            +
            metrics[
                "average_edge"
            ]
            * 0.15
            +
            (
                100.0
                - metrics[
                    "average_uncertainty"
                ]
            )
            * 0.10
            +
            odds_score
            * 0.20
            -
            metrics[
                "correlation_penalty"
            ]
        )

    return score


def optimize_ticket(
    db: Session,
    *,
    strategy: str,
    date_from,
    date_to,
    selections: int | None = None,
    target_odds: float | None = None,
    leagues: list[str] | None = None,
    exclude_leagues: list[str] | None = None,
    min_probability: float | None = None,
):

    strategy = (
        strategy
        .strip()
        .upper()
    )

    if strategy not in STRATEGY_POLICIES:

        strategy = "BALANCED"

    policy = (
        STRATEGY_POLICIES[
            strategy
        ]
    )

    count = (
        selections
        if selections is not None
        else policy[
            "default_selections"
        ]
    )

    count = max(
        policy[
            "min_selections"
        ],
        min(
            count,
            policy[
                "max_selections"
            ],
        ),
    )

    target = (
        float(
            target_odds
        )
        if target_odds
        is not None
        else float(
            policy[
                "default_target_odds"
            ]
        )
    )

    pool = (
        build_candidate_pool(
            db,
            strategy=strategy,
            date_from=date_from,
            date_to=date_to,
            leagues=leagues,
            exclude_leagues=(
                exclude_leagues
            ),
            min_probability=(
                min_probability
            ),
        )
    )

    # Keep combinatorial search bounded.
    search_pool = pool[:20]

    if len(search_pool) < count:

        return {
            "success":
                False,

            "strategy":
                strategy,

            "candidates_found":
                len(pool),

            "requested_selections":
                count,

            "target_odds":
                target,

            "message":
                (
                    "Not enough production-qualified "
                    "signals satisfy the requested "
                    "strategy and filters."
                ),

            "selections":
                [],

            "metrics":
                None,
        }

    best_combo = None
    best_metrics = None
    best_score = None

    for combo in combinations(
        search_pool,
        count,
    ):

        if not combo_is_valid(
            combo,
            max_same_league=(
                policy[
                    "max_same_league"
                ]
            ),
        ):
            continue

        metrics = (
            combo_metrics(
                combo
            )
        )

        score = (
            combo_score(
                metrics=metrics,
                strategy=strategy,
                target_odds=target,
            )
        )

        if (
            best_score is None
            or score > best_score
        ):

            best_combo = combo
            best_metrics = metrics
            best_score = score

    if best_combo is None:

        return {
            "success":
                False,

            "strategy":
                strategy,

            "candidates_found":
                len(pool),

            "requested_selections":
                count,

            "target_odds":
                target,

            "message":
                (
                    "No valid diversified combination "
                    "could be built."
                ),

            "selections":
                [],

            "metrics":
                None,
        }

    result_selections = []

    for item in best_combo:

        signal = (
            item[
                "signal"
            ]
        )

        intelligence = (
            item[
                "intelligence"
            ]
        )

        match = (
            item[
                "match"
            ]
        )

        result_selections.append(
            {
                "signal_id":
                    signal.id,

                "match_id":
                    match.id,

                "match":
                    (
                        f"{match.home_team.name} "
                        f"vs "
                        f"{match.away_team.name}"
                    ),

                "league":
                    item[
                        "league"
                    ],

                "kickoff":
                    (
                        match.match_date
                        .isoformat()
                        if match.match_date
                        else None
                    ),

                "market":
                    item[
                        "market"
                    ],

                "selection":
                    signal.selection,

                "odds":
                    round(
                        float(
                            signal.odds
                        ),
                        2,
                    ),

                "bookmaker":
                    signal.bookmaker,

                "raw_probability":
                    round(
                        float(
                            signal.model_probability
                        ),
                        2,
                    ),

                "calibrated_probability":
                    round(
                        float(
                            intelligence
                            .calibrated_probability
                        ),
                        2,
                    ),

                "edge":
                    round(
                        float(
                            signal.edge
                            or 0.0
                        ),
                        2,
                    ),

                "expected_value":
                    round(
                        float(
                            signal.expected_value
                            or 0.0
                        ),
                        2,
                    ),

                "quality_score":
                    round(
                        float(
                            intelligence
                            .quality_score
                        ),
                        2,
                    ),

                "quality_tier":
                    intelligence
                    .quality_tier,

                "uncertainty":
                    round(
                        float(
                            intelligence
                            .uncertainty
                        ),
                        2,
                    ),
            }
        )

    return {
        "success":
            True,

        "strategy":
            strategy,

        "candidates_found":
            len(pool),

        "requested_selections":
            count,

        "target_odds":
            target,

        "message":
            (
                f"Optimized {strategy} ticket "
                f"from {len(pool)} qualified "
                f"production candidates."
            ),

        "selections":
            result_selections,

        "metrics": {
            "total_odds":
                round(
                    best_metrics[
                        "total_odds"
                    ],
                    2,
                ),

            "estimated_probability":
                round(
                    best_metrics[
                        "estimated_probability"
                    ],
                    2,
                ),

            "naive_probability":
                round(
                    best_metrics[
                        "naive_probability"
                    ],
                    2,
                ),

            "average_quality":
                round(
                    best_metrics[
                        "average_quality"
                    ],
                    2,
                ),

            "average_uncertainty":
                round(
                    best_metrics[
                        "average_uncertainty"
                    ],
                    2,
                ),

            "average_edge":
                round(
                    best_metrics[
                        "average_edge"
                    ],
                    2,
                ),

            "average_ev":
                round(
                    best_metrics[
                        "average_ev"
                    ],
                    2,
                ),

            "correlation_penalty":
                round(
                    best_metrics[
                        "correlation_penalty"
                    ],
                    2,
                ),

            "optimizer_score":
                round(
                    float(
                        best_score
                    ),
                    2,
                ),
        },
    }