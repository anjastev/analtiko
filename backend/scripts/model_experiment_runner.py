from pathlib import Path

import csv
import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import (
    GradientBoostingClassifier,
    HistGradientBoostingClassifier,
    RandomForestClassifier,
)
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

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "market_model_experiments.csv"
)


HOLDOUT_START = pd.Timestamp(
    "2025-04-07"
)


BASE_FEATURES = [
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


RICH_FEATURES = [
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
]


CATEGORICAL_FEATURES = [
    "league",
]


FEATURE_SETS = {
    "BASE": BASE_FEATURES,

    "BASE_PLUS_RICH": (
        BASE_FEATURES
        + RICH_FEATURES
    ),

    "RICH_ONLY": (
        RICH_FEATURES
        + [
            "home_xg",
            "away_xg",
        ]
    ),
}


TARGETS = {
    "OU_25": "over_25",
    "BTTS": "btts",
}


def build_preprocessor(
    numeric_features,
):

    return ColumnTransformer(
        transformers=[
            (
                "numeric",
                StandardScaler(),
                numeric_features,
            ),
            (
                "categorical",
                OneHotEncoder(
                    handle_unknown="ignore"
                ),
                CATEGORICAL_FEATURES,
            ),
        ]
    )


def build_models(
    numeric_features,
):

    return {
        "LOGISTIC": Pipeline(
            steps=[
                (
                    "preprocessor",
                    build_preprocessor(
                        numeric_features
                    ),
                ),
                (
                    "model",
                    LogisticRegression(
                        C=0.1,
                        max_iter=3000,
                    ),
                ),
            ]
        ),

        "RANDOM_FOREST": Pipeline(
            steps=[
                (
                    "preprocessor",
                    build_preprocessor(
                        numeric_features
                    ),
                ),
                (
                    "model",
                    RandomForestClassifier(
                        n_estimators=300,
                        max_depth=6,
                        min_samples_leaf=8,
                        random_state=42,
                        n_jobs=-1,
                    ),
                ),
            ]
        ),

        "GRADIENT_BOOSTING": Pipeline(
            steps=[
                (
                    "preprocessor",
                    build_preprocessor(
                        numeric_features
                    ),
                ),
                (
                    "model",
                    GradientBoostingClassifier(
                        n_estimators=150,
                        learning_rate=0.03,
                        max_depth=2,
                        random_state=42,
                    ),
                ),
            ]
        ),

        "HIST_GRADIENT_BOOSTING": Pipeline(
            steps=[
                (
                    "preprocessor",
                    build_preprocessor(
                        numeric_features
                    ),
                ),
                (
                    "model",
                    HistGradientBoostingClassifier(
                        learning_rate=0.05,
                        max_iter=200,
                        max_leaf_nodes=15,
                        l2_regularization=1.0,
                        random_state=42,
                    ),
                ),
            ]
        ),
    }


def evaluate_selective(
    confidence,
    correct,
    threshold,
):

    mask = (
        confidence
        >= threshold
    )

    count = int(
        mask.sum()
    )

    if count == 0:

        return {
            "count": 0,
            "coverage": 0.0,
            "accuracy": None,
        }

    return {
        "count":
            count,

        "coverage":
            round(
                count
                / len(correct)
                * 100.0,
                4,
            ),

        "accuracy":
            round(
                correct[
                    mask
                ].mean()
                * 100.0,
                4,
            ),
    }


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

    results = []

    print()
    print("=" * 100)
    print(
        "ANALITIKO MARKET MODEL EXPERIMENT RUNNER"
    )
    print("=" * 100)

    for target_name, target_column in (
        TARGETS.items()
    ):

        for (
            feature_set_name,
            numeric_features,
        ) in FEATURE_SETS.items():

            required = (
                numeric_features
                + CATEGORICAL_FEATURES
                + [
                    "match_date",
                    target_column,
                ]
            )

            missing_columns = [
                column
                for column in required
                if column not in df.columns
            ]

            if missing_columns:

                print(
                    f"[SKIP] "
                    f"{target_name} "
                    f"{feature_set_name} "
                    f"missing={missing_columns}"
                )

                continue

            data = (
                df[
                    required
                ]
                .dropna()
                .copy()
            )

            development = (
                data[
                    data[
                        "match_date"
                    ]
                    < HOLDOUT_START
                ]
                .copy()
            )

            holdout = (
                data[
                    data[
                        "match_date"
                    ]
                    >= HOLDOUT_START
                ]
                .copy()
            )

            features = (
                numeric_features
                + CATEGORICAL_FEATURES
            )

            X_train = (
                development[
                    features
                ]
            )

            y_train = (
                development[
                    target_column
                ]
                .astype(int)
            )

            X_test = (
                holdout[
                    features
                ]
            )

            y_test = (
                holdout[
                    target_column
                ]
                .astype(int)
                .to_numpy()
            )

            models = (
                build_models(
                    numeric_features
                )
            )

            for (
                model_name,
                model,
            ) in models.items():

                print()
                print("-" * 100)

                print(
                    f"{target_name} | "
                    f"{feature_set_name} | "
                    f"{model_name}"
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
                    model.classes_
                    if hasattr(
                        model,
                        "classes_"
                    )
                    else
                    model.named_steps[
                        "model"
                    ].classes_
                )

                positive_index = (
                    classes.index(1)
                )

                p_positive = (
                    probabilities[
                        :,
                        positive_index
                    ]
                )

                predicted = (
                    p_positive
                    >= 0.5
                ).astype(int)

                correct = (
                    predicted
                    == y_test
                )

                confidence = (
                    np.maximum(
                        p_positive,
                        1.0
                        - p_positive,
                    )
                    * 100.0
                )

                accuracy = (
                    accuracy_score(
                        y_test,
                        predicted,
                    )
                    * 100.0
                )

                ll = (
                    log_loss(
                        y_test,
                        probabilities,
                        labels=classes,
                    )
                )

                brier = (
                    brier_score_loss(
                        y_test,
                        p_positive,
                    )
                )

                s60 = (
                    evaluate_selective(
                        confidence,
                        correct,
                        60,
                    )
                )

                s65 = (
                    evaluate_selective(
                        confidence,
                        correct,
                        65,
                    )
                )

                s70 = (
                    evaluate_selective(
                        confidence,
                        correct,
                        70,
                    )
                )

                print(
                    f"Accuracy: "
                    f"{accuracy:.2f}%"
                )

                print(
                    f"Log loss: "
                    f"{ll:.4f}"
                )

                print(
                    f"Brier: "
                    f"{brier:.4f}"
                )

                print(
                    f">=60% "
                    f"n={s60['count']} "
                    f"acc={s60['accuracy']}"
                )

                print(
                    f">=65% "
                    f"n={s65['count']} "
                    f"acc={s65['accuracy']}"
                )

                print(
                    f">=70% "
                    f"n={s70['count']} "
                    f"acc={s70['accuracy']}"
                )

                results.append(
                    {
                        "target":
                            target_name,

                        "feature_set":
                            feature_set_name,

                        "model":
                            model_name,

                        "development_rows":
                            len(
                                development
                            ),

                        "holdout_rows":
                            len(
                                holdout
                            ),

                        "accuracy":
                            round(
                                accuracy,
                                4,
                            ),

                        "log_loss":
                            round(
                                ll,
                                6,
                            ),

                        "brier":
                            round(
                                brier,
                                6,
                            ),

                        "n_60":
                            s60[
                                "count"
                            ],

                        "accuracy_60":
                            s60[
                                "accuracy"
                            ],

                        "n_65":
                            s65[
                                "count"
                            ],

                        "accuracy_65":
                            s65[
                                "accuracy"
                            ],

                        "n_70":
                            s70[
                                "count"
                            ],

                        "accuracy_70":
                            s70[
                                "accuracy"
                            ],
                    }
                )

    if results:

        output_df = pd.DataFrame(
            results
        )

        output_df.to_csv(
            OUTPUT_FILE,
            index=False,
        )

        print()
        print("=" * 100)

        print(
            f"Saved: "
            f"{OUTPUT_FILE}"
        )

        print()
        print(
            "TOP BY TARGET"
        )

        for target_name in (
            TARGETS.keys()
        ):

            subset = (
                output_df[
                    output_df[
                        "target"
                    ]
                    == target_name
                ]
                .sort_values(
                    by=[
                        "log_loss",
                        "brier",
                    ],
                    ascending=[
                        True,
                        True,
                    ],
                )
            )

            print()
            print(
                target_name
            )

            print(
                subset[
                    [
                        "feature_set",
                        "model",
                        "accuracy",
                        "log_loss",
                        "brier",
                        "n_60",
                        "accuracy_60",
                        "n_65",
                        "accuracy_65",
                    ]
                ]
                .head(5)
                .to_string(
                    index=False
                )
            )

        print()
        print(
            "STATUS: OK"
        )

        print("=" * 100)


if __name__ == "__main__":
    run()