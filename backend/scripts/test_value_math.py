from app.services.value_calculator import (
    calculate_value_metrics,
)


TESTS = [
    {
        "probability": 80.0,
        "odds": 1.30,
    },
    {
        "probability": 75.0,
        "odds": 1.50,
    },
    {
        "probability": 60.0,
        "odds": 2.00,
    },
]


def run():

    print()
    print("=" * 80)
    print(
        "ANALITIKO VALUE MATH TEST"
    )
    print("=" * 80)

    for test in TESTS:

        result = (
            calculate_value_metrics(
                model_probability=(
                    test[
                        "probability"
                    ]
                ),
                odds=(
                    test[
                        "odds"
                    ]
                ),
            )
        )

        expected_market = (
            100.0
            / test[
                "odds"
            ]
        )

        assert abs(
            result[
                "market_probability"
            ]
            - expected_market
        ) < 0.001

        print()
        print(
            f"Model: "
            f"{test['probability']:.1f}%"
        )

        print(
            f"Odds: "
            f"{test['odds']:.2f}"
        )

        print(
            f"Market: "
            f"{result['market_probability']:.2f}%"
        )

        print(
            f"Edge: "
            f"{result['edge']:+.2f}%"
        )

        print(
            f"EV: "
            f"{result['expected_value']:+.2f}%"
        )

    print()
    print("=" * 80)
    print(
        "STATUS: OK"
    )
    print("=" * 80)


if __name__ == "__main__":
    run()