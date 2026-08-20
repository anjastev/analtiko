from pathlib import Path

import pandas as pd


BASE_DIR = (
    Path(__file__)
    .resolve()
    .parents[1]
)

RESULTS_FILE = (
    BASE_DIR
    / "data"
    / "market_model_experiments.csv"
)


BASELINES = {
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


MIN_SELECTIVE_SAMPLE = 20


def run():

    if not RESULTS_FILE.exists():

        raise FileNotFoundError(
            f"Experiment file not found: "
            f"{RESULTS_FILE}"
        )

    df = pd.read_csv(
        RESULTS_FILE
    )

    print()
    print("=" * 100)
    print(
        "ANALITIKO MARKET MODEL DECISION"
    )
    print("=" * 100)

    for target, baseline in (
        BASELINES.items()
    ):

        subset = (
            df[
                df[
                    "target"
                ]
                == target
            ]
            .copy()
        )

        if subset.empty:

            print()
            print(
                f"{target}: "
                f"NO DATA"
            )

            continue

        subset[
            "score"
        ] = (
            subset[
                "log_loss"
            ]
            +
            subset[
                "brier"
            ]
        )

        best = (
            subset
            .sort_values(
                by=[
                    "score",
                    "accuracy",
                ],
                ascending=[
                    True,
                    False,
                ],
            )
            .iloc[0]
        )

        accuracy_better = (
            best[
                "accuracy"
            ]
            > baseline[
                "accuracy"
            ]
        )

        logloss_better = (
            best[
                "log_loss"
            ]
            < baseline[
                "log_loss"
            ]
        )

        brier_better = (
            best[
                "brier"
            ]
            < baseline[
                "brier"
            ]
        )

        selective_good = False

        if (
            best[
                "n_60"
            ]
            >= MIN_SELECTIVE_SAMPLE
            and
            pd.notna(
                best[
                    "accuracy_60"
                ]
            )
            and
            best[
                "accuracy_60"
            ]
            >= 60.0
        ):

            selective_good = True

        improvements = sum(
            [
                accuracy_better,
                logloss_better,
                brier_better,
                selective_good,
            ]
        )

        if improvements >= 4:

            decision = (
                "PROMOTION CANDIDATE"
            )

        elif improvements >= 2:

            decision = (
                "RESEARCH"
            )

        else:

            decision = (
                "REJECT"
            )

        print()
        print("-" * 100)

        print(
            target
        )

        print(
            f"Best model: "
            f"{best['model']}"
        )

        print(
            f"Feature set: "
            f"{best['feature_set']}"
        )

        print()

        print(
            "Baseline:"
        )

        print(
            f"  Accuracy: "
            f"{baseline['accuracy']:.2f}%"
        )

        print(
            f"  Log loss: "
            f"{baseline['log_loss']:.4f}"
        )

        print(
            f"  Brier: "
            f"{baseline['brier']:.4f}"
        )

        print()

        print(
            "Candidate:"
        )

        print(
            f"  Accuracy: "
            f"{best['accuracy']:.2f}%"
        )

        print(
            f"  Log loss: "
            f"{best['log_loss']:.4f}"
        )

        print(
            f"  Brier: "
            f"{best['brier']:.4f}"
        )

        print(
            f"  >=60 n: "
            f"{int(best['n_60'])}"
        )

        print(
            f"  >=60 accuracy: "
            f"{best['accuracy_60']}"
        )

        print()

        print(
            f"Decision: "
            f"{decision}"
        )

    print()
    print("=" * 100)

    print(
        "NOTE: "
        "This report does not change production models."
    )

    print(
        "STATUS: OK"
    )

    print("=" * 100)


if __name__ == "__main__":
    run()