from pathlib import Path

import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    log_loss,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import (
    OneHotEncoder,
    StandardScaler,
)


DATA_FILE = Path(
    "data/analitiko_dataset.csv"
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

    "form_diff",
    "goals_diff",
    "defense_diff",
    "xg_diff",
    "h2h_diff",

    "home_strength",
    "away_strength",
]

CATEGORICAL_FEATURES = [
    "league",
]


TARGET = "result"

MIN_TRAIN_ROWS = 100


CONFIGS = [
    {
        "name": "C=0.1 no weights",
        "C": 0.1,
        "class_weight": None,
    },
    {
        "name": "C=0.5 no weights",
        "C": 0.5,
        "class_weight": None,
    },
    {
        "name": "C=1.0 no weights",
        "C": 1.0,
        "class_weight": None,
    },
    {
        "name": "C=2.0 no weights",
        "C": 2.0,
        "class_weight": None,
    },

    {
        "name": "C=0.1 balanced",
        "C": 0.1,
        "class_weight": "balanced",
    },
    {
        "name": "C=0.5 balanced",
        "C": 0.5,
        "class_weight": "balanced",
    },
    {
        "name": "C=1.0 balanced",
        "C": 1.0,
        "class_weight": "balanced",
    },
    {
        "name": "C=2.0 balanced",
        "C": 2.0,
        "class_weight": "balanced",
    },
]


def create_pipeline(
    C,
    class_weight,
):

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
                        handle_unknown="ignore"
                    ),
                    CATEGORICAL_FEATURES,
                ),
            ]
        )
    )


    model = LogisticRegression(
        C=C,
        max_iter=3000,
        class_weight=class_weight,
    )


    return Pipeline(
        steps=[
            (
                "preprocessor",
                preprocessor,
            ),
            (
                "model",
                model,
            ),
        ]
    )


def evaluate_config(
    data,
    config,
):

    months = sorted(
        data["month"].unique()
    )


    actual_all = []
    predictions_all = []

    losses = []
    balanced_scores = []

    folds = 0


    for test_month in months:

        train_data = (
            data[
                data["month"]
                < test_month
            ]
        )

        test_data = (
            data[
                data["month"]
                == test_month
            ]
        )


        if len(train_data) < MIN_TRAIN_ROWS:
            continue


        if len(test_data) == 0:
            continue


        if (
            train_data[TARGET]
            .nunique()
            < 2
        ):
            continue


        features = (
            NUMERIC_FEATURES
            + CATEGORICAL_FEATURES
        )


        X_train = train_data[
            features
        ]

        y_train = train_data[
            TARGET
        ]


        X_test = test_data[
            features
        ]

        y_test = test_data[
            TARGET
        ]


        pipeline = (
            create_pipeline(
                C=config["C"],
                class_weight=
                    config[
                        "class_weight"
                    ],
            )
        )


        pipeline.fit(
            X_train,
            y_train,
        )


        predictions = (
            pipeline.predict(
                X_test
            )
        )


        probabilities = (
            pipeline.predict_proba(
                X_test
            )
        )


        classes = (
            pipeline
            .named_steps["model"]
            .classes_
        )


        actual_all.extend(
            y_test.tolist()
        )

        predictions_all.extend(
            predictions.tolist()
        )


        balanced_scores.append(
            balanced_accuracy_score(
                y_test,
                predictions,
            )
        )


        losses.append(
            log_loss(
                y_test,
                probabilities,
                labels=classes,
            )
        )


        folds += 1


    accuracy = (
        accuracy_score(
            actual_all,
            predictions_all,
        )
    )


    average_balanced = (
        sum(balanced_scores)
        / len(balanced_scores)
    )


    average_loss = (
        sum(losses)
        / len(losses)
    )


    return {
        "name":
            config["name"],

        "accuracy":
            accuracy,

        "balanced":
            average_balanced,

        "log_loss":
            average_loss,

        "folds":
            folds,

        "matches":
            len(actual_all),
    }


def run():

    if not DATA_FILE.exists():
        print(
            "Dataset not found."
        )
        return


    data = pd.read_csv(
        DATA_FILE
    )


    data["match_date"] = (
        pd.to_datetime(
            data["match_date"],
            utc=True,
        )
    )


    data = (
        data
        .sort_values(
            "match_date"
        )
        .reset_index(
            drop=True
        )
    )


    data["month"] = (
        data["match_date"]
        .dt.tz_convert(None)
        .dt.to_period("M")
    )


    print()
    print("=" * 75)
    print("ANALITIKO LOGISTIC MODEL TUNING")
    print("=" * 75)

    print(
        f"Dataset rows: "
        f"{len(data)}"
    )


    results = []


    for config in CONFIGS:

        result = (
            evaluate_config(
                data,
                config,
            )
        )

        results.append(
            result
        )


        print()
        print(
            result["name"]
        )

        print(
            f"Accuracy: "
            f"{result['accuracy'] * 100:.1f}%"
        )

        print(
            f"Balanced: "
            f"{result['balanced'] * 100:.1f}%"
        )

        print(
            f"Log loss: "
            f"{result['log_loss']:.4f}"
        )


    results.sort(
        key=lambda item: (
            -item["accuracy"],
            item["log_loss"],
        )
    )


    print()
    print("=" * 75)
    print("RANKING")
    print("=" * 75)


    for index, result in enumerate(
        results,
        start=1,
    ):

        print(
            f"{index}. "
            f"{result['name']} "
            f"| Acc "
            f"{result['accuracy'] * 100:.1f}% "
            f"| Balanced "
            f"{result['balanced'] * 100:.1f}% "
            f"| LogLoss "
            f"{result['log_loss']:.4f}"
        )


if __name__ == "__main__":
    run()