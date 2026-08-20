from __future__ import annotations


def implied_probability(
    odds: float,
) -> float:

    odds = float(
        odds
    )

    if odds <= 1.0:

        raise ValueError(
            "Decimal odds must be greater than 1.0"
        )

    return (
        100.0
        / odds
    )


def calculate_edge(
    *,
    model_probability: float,
    odds: float,
) -> float:

    market_probability = (
        implied_probability(
            odds
        )
    )

    return (
        float(
            model_probability
        )
        - market_probability
    )


def calculate_expected_value(
    *,
    model_probability: float,
    odds: float,
) -> float:

    probability = (
        float(
            model_probability
        )
        / 100.0
    )

    decimal_odds = float(
        odds
    )

    # EV per 1 unit stake:
    #
    # p * profit_if_win
    # -
    # (1-p) * loss_if_lose
    #
    # equivalent to:
    # p * decimal_odds - 1

    ev = (
        probability
        * decimal_odds
        - 1.0
    )

    return (
        ev
        * 100.0
    )


def calculate_value_metrics(
    *,
    model_probability: float,
    odds: float,
):

    market_probability = (
        implied_probability(
            odds
        )
    )

    edge = (
        calculate_edge(
            model_probability=(
                model_probability
            ),
            odds=odds,
        )
    )

    expected_value = (
        calculate_expected_value(
            model_probability=(
                model_probability
            ),
            odds=odds,
        )
    )

    return {
        "market_probability":
            round(
                market_probability,
                6,
            ),

        "edge":
            round(
                edge,
                6,
            ),

        "expected_value":
            round(
                expected_value,
                6,
            ),

        "is_value":
            (
                edge >= 5.0
                and
                expected_value > 0.0
            ),
    }