from dataclasses import dataclass


MIN_VALUE_EDGE = 5.0
MIN_EXPECTED_VALUE = 0.0


@dataclass
class ValueEvaluation:

    model_probability: float

    market_probability: float

    edge: float

    odds: float

    fair_odds: float | None

    expected_value: float

    is_value: bool


def evaluate_value(
    *,
    model_probability: float,
    market_probability: float,
    odds: float,
) -> ValueEvaluation:

    model_probability = float(
        model_probability
    )

    market_probability = float(
        market_probability
    )

    odds = float(
        odds
    )

    edge = (
        model_probability
        - market_probability
    )

    fair_odds = None

    if model_probability > 0:

        fair_odds = (
            100.0
            / model_probability
        )

    # EV in percentage terms.
    #
    # Example:
    # P = 60%
    # odds = 2.00
    #
    # EV = 0.60 * 2.00 - 1
    #    = +0.20
    #    = +20%
    expected_value = (
        (
            model_probability
            / 100.0
        )
        * odds
        - 1.0
    ) * 100.0

    is_value = (
        edge
        >= MIN_VALUE_EDGE
        and
        expected_value
        > MIN_EXPECTED_VALUE
    )

    return ValueEvaluation(
        model_probability=(
            round(
                model_probability,
                4,
            )
        ),

        market_probability=(
            round(
                market_probability,
                4,
            )
        ),

        edge=(
            round(
                edge,
                4,
            )
        ),

        odds=(
            round(
                odds,
                4,
            )
        ),

        fair_odds=(
            round(
                fair_odds,
                4,
            )
            if fair_odds
            is not None
            else None
        ),

        expected_value=(
            round(
                expected_value,
                4,
            )
        ),

        is_value=(
            is_value
        ),
    )