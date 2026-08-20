from app.services.direct_market_value import (
    implied_probability_from_odds,
    calculate_expected_value,
)


def approx(
    a,
    b,
    tolerance=0.01,
):

    return abs(
        a - b
    ) <= tolerance


def run():

    print()
    print("=" * 90)
    print(
        "ANALITIKO DIRECT MARKET VALUE MATH TEST"
    )
    print("=" * 90)

    # ========================================================
    # DIRECT IMPLIED PROBABILITY
    # ========================================================

    tests = [
        (
            1.30,
            76.9231,
        ),

        (
            1.50,
            66.6667,
        ),

        (
            1.65,
            60.6061,
        ),

        (
            2.00,
            50.0000,
        ),

        (
            3.00,
            33.3333,
        ),
    ]

    for (
        odds,
        expected_probability,
    ) in tests:

        actual = (
            implied_probability_from_odds(
                odds
            )
        )

        assert approx(
            actual,
            expected_probability,
        ), (
            f"Odds {odds}: "
            f"expected "
            f"{expected_probability}, "
            f"got {actual}"
        )

        print(
            f"[OK] "
            f"{odds:.2f} -> "
            f"{actual:.2f}%"
        )

    # ========================================================
    # RIED-LIKE EXAMPLE
    # ========================================================

    model_probability = 97.4
    odds = 1.30

    market_probability = (
        implied_probability_from_odds(
            odds
        )
    )

    edge = (
        model_probability
        - market_probability
    )

    ev = (
        calculate_expected_value(
            model_probability=(
                model_probability
            ),
            odds=(
                odds
            ),
        )
    )

    print()
    print(
        "RIED-LIKE EXAMPLE"
    )

    print(
        f"Model: "
        f"{model_probability:.2f}%"
    )

    print(
        f"Odds: "
        f"{odds:.2f}"
    )

    print(
        f"Market: "
        f"{market_probability:.2f}%"
    )

    print(
        f"Edge: "
        f"{edge:+.2f}%"
    )

    print(
        f"EV: "
        f"{ev:+.2f}%"
    )

    assert (
        20.0
        < edge
        < 21.0
    )

    assert (
        26.0
        < ev
        < 27.0
    )

    print()
    print("=" * 90)
    print(
        "STATUS: OK"
    )
    print("=" * 90)


if __name__ == "__main__":
    run()