from pathlib import Path

import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    brier_score_loss,
    log_loss,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import (
    OneHotEncoder,
    StandardScaler,
)


BASE_DIR = (
    Path(__file__)
    .resolve()
    .parents[1]
)

DATASET_FILE = (
    BASE_DIR
    / "data"
    / "analitiko_dataset.csv"
)


HOLDOUT_START = pd.Timestamp(
    "2025-04-07"
)


NUMERIC_FEATURES = [
    "home_form",
    "away_form",
    "home_goals_avg",
    "away_goals_avg",
    "home_goals_against_avg",
    "away_goals_against_avg",
    "home_xg",
    "away_xg",
    "h2h_home_score",
    "h2h_away_score",
    "h2h_matches",
]


CATEGORICAL_FEATURES = [
    "league",
]


FEATURES = (
    NUMERIC_FEATURES
    + CATEGORICAL_FEATURES
)


TARGETS = {
    "OU_25": "over_25",
    "BTTS": "btts",
}


def build_pipeline():

    preprocessor = (
        ColumnTransformer(
            transformers=[
                (
                    "numeric",
                    StandardScaler(),
                    NUMERIC_FEATURES,
                ),
                (
                    "categorical",
                    OneHotEncoder(
                        handle_unknown=(
                            "ignore"
                        )
                    ),
                    CATEGORICAL_FEATURES,
                ),
            ]
        )
    )

    return Pipeline(
        steps=[
            (
                "preprocessor",
                preprocessor,
            ),
            (
                "model",
                LogisticRegression(
                    C=0.1,
                    max_iter=3000,
                ),
            ),
        ]
    )


def run():

    df = pd.read_csv(
        DATASET_FILE
    )

    df[
        "match_date"
    ] = pd.to_datetime(
        df[
            "match_date"
        ]
    )

    print()
    print("=" * 80)
    print(
        "STRICT OOS FOOTBALL MARKET VALIDATION"
    )
    print("=" * 80)

    for name, target in (
        TARGETS.items()
    ):

        model_df = (
            df[
                FEATURES
                + [
                    "match_date",
                    target,
                ]
            ]
            .dropna()
            .copy()
        )

        development = (
            model_df[
                model_df[
                    "match_date"
                ]
                < HOLDOUT_START
            ]
            .copy()
        )

        holdout = (
            model_df[
                model_df[
                    "match_date"
                ]
                >= HOLDOUT_START
            ]
            .copy()
        )

        X_train = (
            development[
                FEATURES
            ]
        )

        y_train = (
            development[
                target
            ]
            .astype(int)
        )

        X_test = (
            holdout[
                FEATURES
            ]
        )

        y_test = (
            holdout[
                target
            ]
            .astype(int)
            .to_numpy()
        )

        model = (
            build_pipeline()
        )

        model.fit(
            X_train,
            y_train,
        )

        probabilities = (
            model.predict_proba(
                X_test
            )
        )

        classes = list(
            model
            .named_steps["model"]
            .classes_
        )

        positive_index = (
            classes.index(1)
        )

        positive_probability = (
            probabilities[
                :,
                positive_index
            ]
        )

        predicted = (
            positive_probability
            >= 0.5
        ).astype(int)

        correct = (
            predicted
            == y_test
        )

        confidence = (
            np.maximum(
                positive_probability,
                1.0
                - positive_probability,
            )
            * 100.0
        )

        print()
        print("-" * 80)

        print(
            f"{name}"
        )

        print(
            f"Development rows: "
            f"{len(development)}"
        )

        print(
            f"Holdout rows: "
            f"{len(holdout)}"
        )

        print(
            f"Accuracy: "
            f"{accuracy_score(y_test, predicted) * 100:.1f}%"
        )

        print(
            f"Log loss: "
            f"{log_loss(y_test, probabilities, labels=classes):.4f}"
        )

        print(
            f"Brier: "
            f"{brier_score_loss(y_test, positive_probability):.4f}"
        )

        print(
            f"Positive rate: "
            f"{y_test.mean() * 100:.1f}%"
        )

        print()

        print(
            "SELECTIVE ACCURACY"
        )

        for threshold in [
            55,
            60,
            65,
            70,
            75,
            80,
            85,
        ]:

            mask = (
                confidence
                >= threshold
            )

            count = int(
                mask.sum()
            )

            if count == 0:

                print(
                    f">= {threshold}% "
                    f"| n=0"
                )

                continue

            coverage = (
                count
                / len(y_test)
                * 100.0
            )

            selective_accuracy = (
                correct[
                    mask
                ].mean()
                * 100.0
            )

            print(
                f">= {threshold}% "
                f"| n={count:<4} "
                f"| coverage="
                f"{coverage:>5.1f}% "
                f"| accuracy="
                f"{selective_accuracy:>5.1f}%"
            )

    print()
    print("=" * 80)
    print(
        "STRICT VALIDATION COMPLETE"
    )
    print("=" * 80)


if __name__ == "__main__":
    run()