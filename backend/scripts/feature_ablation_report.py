from pathlib import Path

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


GROUPS = {
    "BASE": [
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
    ],

    "SHORT_FORM": [
        "home_form_3",
        "away_form_3",
        "recent_form_diff_3",
    ],

    "VENUE_ATTACK_DEFENSE": [
        "home_home_ppg",
        "away_away_ppg",
        "home_home_goals_avg",
        "away_away_goals_avg",
        "home_home_conceded_avg",
        "away_away_conceded_avg",
        "home_home_goal_diff_avg",
        "away_away_goal_diff_avg",
    ],

    "VENUE_RATES": [
        "home_home_clean_sheet_rate",
        "away_away_clean_sheet_rate",
        "home_home_failed_score_rate",
        "away_away_failed_score_rate",
        "home_home_win_rate",
        "away_away_win_rate",
        "home_away_context_diff",
    ],
}


TARGETS = {
    "OU_25": "over_25",
    "BTTS": "btts",
}


def build_model(
    numeric_features,
):

    preprocessor = (
        ColumnTransformer(
            transformers=[
                (
                    "numeric",
                    StandardScaler(),
                    numeric_features,
                ),
                (
                    "league",
                    OneHotEncoder(
                        handle_unknown="ignore"
                    ),
                    [
                        "league"
                    ],
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


def evaluate(
    df,
    target_column,
    features,
):

    required = (
        features
        + [
            "league",
            "match_date",
            target_column,
        ]
    )

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
    )

    holdout = (
        data[
            data[
                "match_date"
            ]
            >= HOLDOUT_START
        ]
    )

    model = (
        build_model(
            features
        )
    )

    X_train = (
        development[
            features
            + [
                "league"
            ]
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
            + [
                "league"
            ]
        ]
    )

    y_test = (
        holdout[
            target_column
        ]
        .astype(int)
        .to_numpy()
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

    predictions = (
        p_positive
        >= 0.5
    ).astype(int)

    return {
        "accuracy":
            accuracy_score(
                y_test,
                predictions,
            )
            * 100.0,

        "log_loss":
            log_loss(
                y_test,
                probabilities,
                labels=classes,
            ),

        "brier":
            brier_score_loss(
                y_test,
                p_positive,
            ),

        "rows":
            len(
                holdout
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

    experiments = {
        "BASE_ONLY":
            GROUPS[
                "BASE"
            ],

        "BASE_SHORT":
            GROUPS[
                "BASE"
            ]
            + GROUPS[
                "SHORT_FORM"
            ],

        "BASE_VENUE_ATTACK_DEFENSE":
            GROUPS[
                "BASE"
            ]
            + GROUPS[
                "VENUE_ATTACK_DEFENSE"
            ],

        "BASE_VENUE_RATES":
            GROUPS[
                "BASE"
            ]
            + GROUPS[
                "VENUE_RATES"
            ],

        "BASE_ALL_VENUE":
            GROUPS[
                "BASE"
            ]
            + GROUPS[
                "VENUE_ATTACK_DEFENSE"
            ]
            + GROUPS[
                "VENUE_RATES"
            ],

        "ALL":
            GROUPS[
                "BASE"
            ]
            + GROUPS[
                "SHORT_FORM"
            ]
            + GROUPS[
                "VENUE_ATTACK_DEFENSE"
            ]
            + GROUPS[
                "VENUE_RATES"
            ],
    }

    print()
    print("=" * 100)
    print(
        "ANALITIKO FEATURE ABLATION REPORT"
    )
    print("=" * 100)

    for target_name, target_column in (
        TARGETS.items()
    ):

        print()
        print(
            target_name
        )

        print("-" * 100)

        rows = []

        for (
            experiment_name,
            features,
        ) in experiments.items():

            result = (
                evaluate(
                    df=df,
                    target_column=(
                        target_column
                    ),
                    features=features,
                )
            )

            rows.append(
                {
                    "experiment":
                        experiment_name,

                    "features":
                        len(features),

                    "accuracy":
                        round(
                            result[
                                "accuracy"
                            ],
                            2,
                        ),

                    "log_loss":
                        round(
                            result[
                                "log_loss"
                            ],
                            4,
                        ),

                    "brier":
                        round(
                            result[
                                "brier"
                            ],
                            4,
                        ),

                    "holdout_rows":
                        result[
                            "rows"
                        ],
                }
            )

        report = (
            pd.DataFrame(
                rows
            )
            .sort_values(
                by=[
                    "log_loss",
                    "brier",
                ]
            )
        )

        print(
            report.to_string(
                index=False
            )
        )

    print()
    print("=" * 100)
    print(
        "STATUS: OK"
    )
    print("=" * 100)


if __name__ == "__main__":
    run()