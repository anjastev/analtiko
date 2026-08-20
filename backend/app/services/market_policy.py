from dataclasses import dataclass


# ============================================================
# MARKET STATUS
# ============================================================

STATUS_ACTIVE = "ACTIVE"
STATUS_RESEARCH = "RESEARCH"
STATUS_DISABLED = "DISABLED"


# ============================================================
# POLICY DTO
# ============================================================

@dataclass(frozen=True)
class MarketPolicy:
    code: str
    status: str
    min_signal_probability: float | None
    allow_signals: bool
    allow_combinations: bool
    reason: str


# ============================================================
# CURRENT VALIDATED POLICY
# ============================================================

MARKET_POLICIES = {
    "DC": MarketPolicy(
        code="DC",
        status=STATUS_ACTIVE,
        min_signal_probability=75.0,
        allow_signals=True,
        allow_combinations=True,
        reason=(
            "Derived from frozen 1X2 model. "
            "Currently allowed as production candidate."
        ),
    ),

    "OU_25": MarketPolicy(
        code="OU_25",
        status=STATUS_RESEARCH,
        min_signal_probability=65.0,
        allow_signals=False,
        allow_combinations=False,
        reason=(
            "Strict OOS accuracy is modest. "
            "75% accuracy at >=65% confidence had only n=4, "
            "which is insufficient for production."
        ),
    ),

    "BTTS": MarketPolicy(
        code="BTTS",
        status=STATUS_DISABLED,
        min_signal_probability=None,
        allow_signals=False,
        allow_combinations=False,
        reason=(
            "Strict OOS performance is close to random "
            "and high-confidence performance is not reliable."
        ),
    ),
}


def get_market_policy(
    market_code: str,
) -> MarketPolicy:

    policy = MARKET_POLICIES.get(
        market_code
    )

    if policy is None:

        return MarketPolicy(
            code=market_code,
            status=STATUS_DISABLED,
            min_signal_probability=None,
            allow_signals=False,
            allow_combinations=False,
            reason=(
                "No validated market policy exists."
            ),
        )

    return policy


def market_allows_signals(
    market_code: str,
) -> bool:

    return get_market_policy(
        market_code
    ).allow_signals


def market_allows_combinations(
    market_code: str,
) -> bool:

    return get_market_policy(
        market_code
    ).allow_combinations