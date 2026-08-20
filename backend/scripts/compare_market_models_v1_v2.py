V1_RESULTS = {
    "OU_25": {
        "accuracy": 53.4,
        "log_loss": 0.6849,
        "brier": 0.2459,
    },

    "BTTS": {
        "accuracy": 50.9,
        "log_loss": 0.7030,
        "brier": 0.2548,
    },
}


def run():

    print()
    print("=" * 80)
    print(
        "ANALITIKO MARKET MODEL BENCHMARK"
    )
    print("=" * 80)

    print()
    print(
        "CURRENT STRICT V1 BASELINES"
    )

    for name, metrics in (
        V1_RESULTS.items()
    ):

        print()
        print(
            name
        )

        print(
            f"  Accuracy: "
            f"{metrics['accuracy']:.1f}%"
        )

        print(
            f"  Log loss: "
            f"{metrics['log_loss']:.4f}"
        )

        print(
            f"  Brier: "
            f"{metrics['brier']:.4f}"
        )

    print()
    print(
        "Compare these values with "
        "evaluate_market_models_v2_strict output."
    )

    print()
    print(
        "Promotion requires:"
    )

    print(
        "  1. Better or clearly competitive accuracy"
    )

    print(
        "  2. Lower log loss"
    )

    print(
        "  3. Lower Brier score"
    )

    print(
        "  4. Better selective accuracy with useful sample size"
    )

    print(
        "  5. Live feature coverage must be acceptable"
    )

    print()
    print(
        "NO MODEL IS AUTO-PROMOTED."
    )

    print("=" * 80)


if __name__ == "__main__":
    run()