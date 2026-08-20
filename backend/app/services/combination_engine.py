from dataclasses import dataclass


# ============================================================
# GLOBAL CONFIG
# ============================================================

MAX_SELECTIONS_PER_MATCH = 1


# ============================================================
# STRATEGIES
# ============================================================

STRATEGIES = {
    "SAFE": {
        "min_probability": 75.0,
        "min_signal_rank": 1,
        "prefer_positive_edge": True,
        "default_selections": 3,
        "max_selections": 3,
    },

    "BALANCED": {
        "min_probability": 70.0,
        "min_signal_rank": 1,
        "prefer_positive_edge": True,
        "default_selections": 4,
        "max_selections": 5,
    },

    "AGGRESSIVE": {
        "min_probability": 60.0,
        "min_signal_rank": 0,
        "prefer_positive_edge": True,
        "default_selections": 5,
        "max_selections": 6,
    },
}


# ============================================================
# DTO
# ============================================================
@dataclass
class CombinationCandidate:
    signal_id: int
    match_id: int

    market_code: str
    selection: str
    signal_type: str

    probability: float
    edge: float | None

    score: float

# ============================================================
# SIGNAL RANK
# ============================================================

def signal_rank(
    signal_type: str,
) -> int:

    mapping = {
        "ULTRA": 3,
        "ELITE": 2,
        "STRONG": 1,
    }

    return mapping.get(
        signal_type,
        0,
    )


# ============================================================
# CANDIDATE SCORE
# ============================================================

def calculate_candidate_score(
    probability: float,
    signal_type: str,
    edge: float | None,
) -> float:

    probability = float(
        probability
    )

    score = probability

    rank_bonus = {
        "ULTRA": 30.0,
        "ELITE": 20.0,
        "STRONG": 10.0,
    }

    score += rank_bonus.get(
        signal_type,
        0.0,
    )

    # ========================================================
    # EDGE
    # ========================================================

    if edge is not None:

        edge = float(
            edge
        )

        # Limit edge influence.
        edge_bonus = max(
            min(
                edge,
                20.0,
            ),
            -20.0,
        )

        score += edge_bonus

    return round(
        score,
        4,
    )


# ============================================================
# STRATEGY CONFIG
# ============================================================

def get_strategy_config(
    strategy: str,
):

    strategy = (
        strategy
        .strip()
        .upper()
    )

    config = STRATEGIES.get(
        strategy
    )

    if config is None:

        raise ValueError(
            f"Unknown strategy: {strategy}"
        )

    return config


# ============================================================
# FILTER
# ============================================================

def candidate_allowed(
    candidate: CombinationCandidate,
    strategy: str,
) -> bool:

    config = (
        get_strategy_config(
            strategy
        )
    )

    if (
        candidate.probability
        < config[
            "min_probability"
        ]
    ):
        return False

    rank = signal_rank(
        candidate.signal_type
    )

    if (
        rank
        < config[
            "min_signal_rank"
        ]
    ):
        return False

    return True


# ============================================================
# SORTING
# ============================================================

def candidate_sort_key(
    candidate: CombinationCandidate,
    strategy: str,
):

    config = (
        get_strategy_config(
            strategy
        )
    )

    positive_edge = 0

    if (
        candidate.edge
        is not None
        and candidate.edge > 0
    ):
        positive_edge = 1

    if config[
        "prefer_positive_edge"
    ]:

        return (
            positive_edge,
            candidate.score,
            candidate.probability,
        )

    return (
        candidate.score,
        candidate.probability,
    )


# ============================================================
# SELECTION
# ============================================================

def select_candidates(
    candidates: list[
        CombinationCandidate
    ],
    strategy: str,
    number_of_selections: int | None = None,
) -> list[
    CombinationCandidate
]:

    strategy = (
        strategy
        .strip()
        .upper()
    )

    config = (
        get_strategy_config(
            strategy
        )
    )

    if number_of_selections is None:

        number_of_selections = (
            config[
                "default_selections"
            ]
        )

    number_of_selections = min(
        number_of_selections,
        config[
            "max_selections"
        ],
    )

    filtered = [
        candidate
        for candidate in candidates
        if candidate_allowed(
            candidate,
            strategy,
        )
    ]

    ordered = sorted(
        filtered,
        key=lambda item:
            candidate_sort_key(
                item,
                strategy,
            ),
        reverse=True,
    )

    selected = []

    used_matches = set()

    for candidate in ordered:

        # ====================================================
        # CORRELATION PROTECTION V1
        # ====================================================

        if (
            MAX_SELECTIONS_PER_MATCH
            == 1
            and candidate.match_id
            in used_matches
        ):
            continue

        selected.append(
            candidate
        )

        used_matches.add(
            candidate.match_id
        )

        if (
            len(selected)
            >= number_of_selections
        ):
            break

    return selected