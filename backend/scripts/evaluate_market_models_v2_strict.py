from pathlib import Path

import numpy as np
import pandas as pd

from sklearn.compose import (
    ColumnTransformer,
)
from sklearn.linear_model import (
    LogisticRegression,
)
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

    "home_form_3",
    "away_form_3",
    "recent_form_diff_3",

    "home_home_ppg",
    "away_away_ppg",

    "home_home_goals_avg",
    "away_away_goals_avg",

    "home_home_conceded_avg",
    "away_away_conceded_avg",

    "home_home_goal_diff_avg",
    "away_away_goal_diff_avg",

    "home_home_clean_sheet_rate",
    "away_away_clean_sheet_rate",

    "home_home_failed_score_rate",
    "away_away_failed_score_rate",

    "home_home_win_rate",
    "away_away_win_rate",

    "home_away_context_diff",

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
    "OU_25_V2": "over_25",
    "BTTS_V2": "btts",
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
        "STRICT OOS MARKET V2 VALIDATION"
    )
    print("=" * 80)

    for model_name, target in (
        TARGETS.items()
    ):

        required = (
            FEATURES
            + [
                "match_date",
                target,
            ]
        )

        model_df = (
            df[
                required
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
        )

        holdout = (
            model_df[
                model_df[
                    "match_date"
                ]
                >= HOLDOUT_START
            ]
        )

        model = (
            build_pipeline()
        )

        model.fit(
            development[
                FEATURES
            ],
            development[
                target
            ].astype(int),
        )

        probabilities = (
            model.predict_proba(
                holdout[
                    FEATURES
                ]
            )
        )

        classes = list(
            model
            .named_steps[
                "model"
            ]
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

        y_true = (
            holdout[
                target
            ]
            .astype(int)
            .to_numpy()
        )

        prediction = (
            positive_probability
            >= 0.5
        ).astype(int)

        correct = (
            prediction == y_true
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
            model_name
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
            f"{accuracy_score(y_true, prediction) * 100:.1f}%"
        )

        print(
            f"Log loss: "
            f"{log_loss(y_true, probabilities, labels=classes):.4f}"
        )

        print(
            f"Brier: "
            f"{brier_score_loss(y_true, positive_probability):.4f}"
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
                    "| n=0"
                )

                continue

            coverage = (
                count
                / len(y_true)
                * 100.0
            )

            accuracy = (
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
                f"{accuracy:>5.1f}%"
            )

    print()
    print("=" * 80)

    print(
        "STATUS: OK"
    )

    print("=" * 80)


if __name__ == "__main__":
    run()