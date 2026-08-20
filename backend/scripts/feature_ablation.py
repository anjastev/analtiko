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

TARGET = "result"

MIN_TRAIN_ROWS = 100


# ============================================================
# FEATURE GROUPS
# ============================================================

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


DIFF_FEATURES = [
    "form_diff",
    "goals_diff",
    "defense_diff",
    "xg_diff",
    "h2h_diff",
    "home_strength",
    "away_strength",
]


RECENT_FEATURES = [
    "home_form_3",
    "away_form_3",
    "recent_form_diff_3",
]


VENUE_BASIC_FEATURES = [
    "home_home_ppg",
    "away_away_ppg",

    "home_home_goals_avg",
    "away_away_goals_avg",

    "home_home_conceded_avg",
    "away_away_conceded_avg",

    "home_away_context_diff",
]


VENUE_ADVANCED_FEATURES = [
    "home_home_goal_diff_avg",
    "away_away_goal_diff_avg",

    "home_home_clean_sheet_rate",
    "away_away_clean_sheet_rate",

    "home_home_failed_score_rate",
    "away_away_failed_score_rate",

    "home_home_win_rate",
    "away_away_win_rate",
]


CATEGORICAL_FEATURES = [
    "league",
]


EXPERIMENTS = {
    "BASE":
        BASE_FEATURES,

    "BASE + DIFF":
        BASE_FEATURES
        + DIFF_FEATURES,

    "BASE + RECENT":
        BASE_FEATURES
        + RECENT_FEATURES,

    "BASE + VENUE BASIC":
        BASE_FEATURES
        + VENUE_BASIC_FEATURES,

    "BASE + VENUE ADVANCED":
        BASE_FEATURES
        + VENUE_ADVANCED_FEATURES,

    "BASE + DIFF + RECENT":
        BASE_FEATURES
        + DIFF_FEATURES
        + RECENT_FEATURES,

    "BASE + DIFF + VENUE BASIC":
        BASE_FEATURES
        + DIFF_FEATURES
        + VENUE_BASIC_FEATURES,

    "BASE + RECENT + VENUE BASIC":
        BASE_FEATURES
        + RECENT_FEATURES
        + VENUE_BASIC_FEATURES,

    "ALL V3":
        BASE_FEATURES
        + DIFF_FEATURES
        + RECENT_FEATURES
        + VENUE_BASIC_FEATURES
        + VENUE_ADVANCED_FEATURES,
}


def create_pipeline(
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
        C=0.1,
        max_iter=3000,
        class_weight=None,
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


def evaluate_features(
    data,
    numeric_features,
):

    months = sorted(
        data["month"].unique()
    )

    actual_all = []
    predictions_all = []

    balanced_scores = []
    losses = []

    fold_accuracies = []

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


        if (
            len(train_data)
            < MIN_TRAIN_ROWS
        ):
            continue


        if len(test_data) == 0:
            continue


        if (
            train_data[
                TARGET
            ].nunique()
            < 2
        ):
            continue


        feature_columns = (
            numeric_features
            + CATEGORICAL_FEATURES
        )


        X_train = (
            train_data[
                feature_columns
            ]
        )

        y_train = (
            train_data[
                TARGET
            ]
        )


        X_test = (
            test_data[
                feature_columns
            ]
        )

        y_test = (
            test_data[
                TARGET
            ]
        )


        pipeline = (
            create_pipeline(
                numeric_features
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


        fold_accuracy = (
            accuracy_score(
                y_test,
                predictions,
            )
        )


        fold_accuracies.append(
            fold_accuracy
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


        actual_all.extend(
            y_test.tolist()
        )


        predictions_all.extend(
            predictions.tolist()
        )


        folds += 1


    overall_accuracy = (
        accuracy_score(
            actual_all,
            predictions_all,
        )
    )


    average_monthly_accuracy = (
        sum(
            fold_accuracies
        )
        / len(
            fold_accuracies
        )
    )


    average_balanced = (
        sum(
            balanced_scores
        )
        / len(
            balanced_scores
        )
    )


    average_loss = (
        sum(
            losses
        )
        / len(
            losses
        )
    )


    return {
        "accuracy":
            overall_accuracy,

        "monthly_accuracy":
            average_monthly_accuracy,

        "balanced":
            average_balanced,

        "log_loss":
            average_loss,

        "folds":
            folds,

        "matches":
            len(
                actual_all
            ),

        "feature_count":
            len(
                numeric_features
            ),
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
        data[
            "match_date"
        ]
        .dt.tz_convert(
            None
        )
        .dt.to_period(
            "M"
        )
    )


    print()
    print("=" * 80)
    print(
        "ANALITIKO FEATURE ABLATION"
    )
    print("=" * 80)

    print(
        f"Dataset rows: "
        f"{len(data)}"
    )


    results = []


    for (
        name,
        features,
    ) in EXPERIMENTS.items():

        print()
        print(
            f"Testing: {name}"
        )

        print(
            f"Features: "
            f"{len(features)}"
        )


        missing = [
            feature
            for feature
            in features
            if feature
            not in data.columns
        ]


        if missing:

            print(
                f"SKIPPED - "
                f"missing: "
                f"{missing}"
            )

            continue


        result = (
            evaluate_features(
                data,
                features,
            )
        )


        result["name"] = name


        results.append(
            result
        )


        print(
            f"Overall accuracy: "
            f"{result['accuracy'] * 100:.1f}%"
        )

        print(
            f"Monthly accuracy: "
            f"{result['monthly_accuracy'] * 100:.1f}%"
        )

        print(
            f"Balanced: "
            f"{result['balanced'] * 100:.1f}%"
        )

        print(
            f"Log loss: "
            f"{result['log_loss']:.4f}"
        )


    # ========================================================
    # RANKING
    # ========================================================

    results.sort(
        key=lambda item: (
            -item[
                "accuracy"
            ],
            item[
                "log_loss"
            ],
        )
    )


    print()
    print("=" * 80)
    print("FINAL RANKING")
    print("=" * 80)

    print()

    print(
        f"{'#':<4}"
        f"{'Feature Set':<30}"
        f"{'Features':>10}"
        f"{'Accuracy':>12}"
        f"{'Balanced':>12}"
        f"{'LogLoss':>12}"
    )


    for (
        index,
        result,
    ) in enumerate(
        results,
        start=1,
    ):

        print(
            f"{index:<4}"
            f"{result['name']:<30}"
            f"{result['feature_count']:>10}"
            f"{result['accuracy'] * 100:>11.1f}%"
            f"{result['balanced'] * 100:>11.1f}%"
            f"{result['log_loss']:>12.4f}"
        )


    print()
    print("=" * 80)


if __name__ == "__main__":
    run()