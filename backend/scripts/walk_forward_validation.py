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

    "home_xg",
    "away_xg",

    "h2h_home_score",
    "h2h_away_score",
    "h2h_matches",
]


CATEGORICAL_FEATURES = [
    "league",
]


TARGET = "result"


# Minimum amount of historical data
# required before testing a month.
MIN_TRAIN_ROWS = 100


# Current experimental threshold
# from our previous backtest.
ANALITIKO_SCORE_THRESHOLD = 0.35


def create_pipeline():

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


    model = (
        LogisticRegression(
            C=0.1,
            max_iter=3000,
            class_weight=None,
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
                model,
            ),
        ]
    )


def calculate_analitiko_scores(
    probabilities,
):

    confidence_scores = (
        probabilities.max(
            axis=1
        )
    )


    sorted_probabilities = (
        probabilities.copy()
    )


    sorted_probabilities.sort(
        axis=1
    )


    margins = (
        sorted_probabilities[:, -1]
        -
        sorted_probabilities[:, -2]
    )


    scores = (
        confidence_scores * 0.70
        +
        margins * 0.30
    )


    return (
        confidence_scores,
        margins,
        scores,
    )


def run():

    # ========================================================
    # LOAD DATA
    # ========================================================

    if not DATA_FILE.exists():

        print(
            f"Dataset not found: "
            f"{DATA_FILE.resolve()}"
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


    feature_columns = (
        NUMERIC_FEATURES
        + CATEGORICAL_FEATURES
    )


    missing_columns = [
        column
        for column in feature_columns
        if column not in data.columns
    ]


    if missing_columns:

        print(
            "Missing dataset columns:"
        )

        for column in missing_columns:
            print(
                f"- {column}"
            )

        return


    print()
    print("=" * 75)
    print("ANALITIKO WALK-FORWARD VALIDATION")
    print("=" * 75)

    print(
        f"Dataset rows: "
        f"{len(data)}"
    )

    print(
        f"Period: "
        f"{data['match_date'].min()}"
    )

    print(
        "-> "
        f"{data['match_date'].max()}"
    )


    # ========================================================
    # CREATE MONTH KEY
    # ========================================================

    # Remove timezone because Period conversion
    # does not preserve timezone information.
    data["month"] = (
        data["match_date"]
        .dt.tz_convert(None)
        .dt.to_period("M")
    )


    months = (
        sorted(
            data["month"]
            .unique()
        )
    )


    # ========================================================
    # RESULT STORAGE
    # ========================================================

    fold_results = []

    all_actual = []
    all_predictions = []

    all_selected_actual = []
    all_selected_predictions = []


    # ========================================================
    # WALK FORWARD
    # ========================================================

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


        # ====================================================
        # TRAIN
        # ====================================================

        pipeline = (
            create_pipeline()
        )


        pipeline.fit(
            X_train,
            y_train,
        )


        # ====================================================
        # PREDICT
        # ====================================================

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


        # ====================================================
        # METRICS
        # ====================================================

        accuracy = (
            accuracy_score(
                y_test,
                predictions,
            )
        )


        balanced_accuracy = (
            balanced_accuracy_score(
                y_test,
                predictions,
            )
        )


        loss = (
            log_loss(
                y_test,
                probabilities,
                labels=classes,
            )
        )


        (
            confidence_scores,
            margins,
            analitiko_scores,
        ) = calculate_analitiko_scores(
            probabilities
        )


        # ====================================================
        # STRONG PICKS
        # ====================================================

        strong_mask = (
            analitiko_scores
            >= ANALITIKO_SCORE_THRESHOLD
        )


        strong_count = int(
            strong_mask.sum()
        )


        if strong_count > 0:

            strong_actual = (
                y_test.to_numpy()[
                    strong_mask
                ]
            )


            strong_predictions = (
                predictions[
                    strong_mask
                ]
            )


            strong_accuracy = (
                accuracy_score(
                    strong_actual,
                    strong_predictions,
                )
            )


            all_selected_actual.extend(
                strong_actual.tolist()
            )


            all_selected_predictions.extend(
                strong_predictions.tolist()
            )

        else:

            strong_accuracy = None


        coverage = (
            strong_count
            / len(test_data)
            * 100
        )


        # ====================================================
        # SAVE GLOBAL RESULTS
        # ====================================================

        all_actual.extend(
            y_test.tolist()
        )


        all_predictions.extend(
            predictions.tolist()
        )


        fold_results.append(
            {
                "month":
                    str(test_month),

                "train_rows":
                    len(train_data),

                "test_rows":
                    len(test_data),

                "accuracy":
                    accuracy,

                "balanced_accuracy":
                    balanced_accuracy,

                "log_loss":
                    loss,

                "strong_count":
                    strong_count,

                "strong_accuracy":
                    strong_accuracy,

                "coverage":
                    coverage,
            }
        )


        # ====================================================
        # PRINT MONTH
        # ====================================================

        print()
        print("-" * 75)

        print(
            f"Test month: "
            f"{test_month}"
        )

        print(
            f"Train: "
            f"{len(train_data)}"
            f" | "
            f"Test: "
            f"{len(test_data)}"
        )

        print(
            f"Accuracy: "
            f"{accuracy * 100:.1f}%"
        )

        print(
            f"Balanced: "
            f"{balanced_accuracy * 100:.1f}%"
        )

        print(
            f"Log loss: "
            f"{loss:.4f}"
        )


        if strong_count > 0:

            print(
                f"Score >= "
                f"{ANALITIKO_SCORE_THRESHOLD * 100:.0f}: "
                f"{strong_count} matches"
                f" | "
                f"Coverage "
                f"{coverage:.1f}%"
                f" | "
                f"Accuracy "
                f"{strong_accuracy * 100:.1f}%"
            )

        else:

            print(
                f"Score >= "
                f"{ANALITIKO_SCORE_THRESHOLD * 100:.0f}: "
                f"0 matches"
            )


    # ========================================================
    # FINAL RESULTS
    # ========================================================

    print()
    print("=" * 75)
    print("WALK-FORWARD SUMMARY")
    print("=" * 75)


    if not fold_results:

        print(
            "No valid folds generated."
        )

        return


    total_test_matches = (
        len(
            all_actual
        )
    )


    overall_accuracy = (
        accuracy_score(
            all_actual,
            all_predictions,
        )
    )


    print()
    print(
        f"Folds: "
        f"{len(fold_results)}"
    )

    print(
        f"Total test matches: "
        f"{total_test_matches}"
    )

    print(
        f"Overall accuracy: "
        f"{overall_accuracy * 100:.1f}%"
    )


    # ========================================================
    # AVERAGE MONTHLY METRICS
    # ========================================================

    average_accuracy = (
        sum(
            item["accuracy"]
            for item
            in fold_results
        )
        / len(fold_results)
    )


    average_balanced = (
        sum(
            item["balanced_accuracy"]
            for item
            in fold_results
        )
        / len(fold_results)
    )


    average_loss = (
        sum(
            item["log_loss"]
            for item
            in fold_results
        )
        / len(fold_results)
    )


    print()
    print(
        f"Average monthly accuracy: "
        f"{average_accuracy * 100:.1f}%"
    )

    print(
        f"Average balanced accuracy: "
        f"{average_balanced * 100:.1f}%"
    )

    print(
        f"Average log loss: "
        f"{average_loss:.4f}"
    )


    # ========================================================
    # STRONG PICK SUMMARY
    # ========================================================

    print()
    print("=" * 75)
    print("STRONG PICK SUMMARY")
    print("=" * 75)


    total_strong = (
        len(
            all_selected_actual
        )
    )


    if total_strong > 0:

        strong_accuracy = (
            accuracy_score(
                all_selected_actual,
                all_selected_predictions,
            )
        )


        strong_coverage = (
            total_strong
            / total_test_matches
            * 100
        )


        print()
        print(
            f"Threshold: "
            f"Analitiko Score >= "
            f"{ANALITIKO_SCORE_THRESHOLD * 100:.0f}"
        )

        print(
            f"Selected matches: "
            f"{total_strong}"
        )

        print(
            f"Coverage: "
            f"{strong_coverage:.1f}%"
        )

        print(
            f"Accuracy: "
            f"{strong_accuracy * 100:.1f}%"
        )

    else:

        print()
        print(
            "No strong predictions "
            "were generated."
        )


    # ========================================================
    # MONTH TABLE
    # ========================================================

    print()
    print("=" * 75)
    print("MONTHLY SUMMARY")
    print("=" * 75)

    print()

    print(
        f"{'Month':<10}"
        f"{'Test':>7}"
        f"{'Acc':>9}"
        f"{'Strong':>9}"
        f"{'StrongAcc':>12}"
    )


    for item in fold_results:

        if (
            item[
                "strong_accuracy"
            ]
            is not None
        ):

            strong_accuracy_text = (
                f"{item['strong_accuracy'] * 100:.1f}%"
            )

        else:

            strong_accuracy_text = "-"


        print(
            f"{item['month']:<10}"
            f"{item['test_rows']:>7}"
            f"{item['accuracy'] * 100:>8.1f}%"
            f"{item['strong_count']:>9}"
            f"{strong_accuracy_text:>12}"
        )


    print()
    print("=" * 75)
    print("VALIDATION COMPLETE")
    print("=" * 75)


if __name__ == "__main__":
    run()