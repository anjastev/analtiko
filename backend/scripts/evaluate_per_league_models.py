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
from sklearn.preprocessing import StandardScaler


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

    "form_diff",
    "goals_diff",
    "defense_diff",
    "xg_diff",
    "h2h_diff",
    "home_strength",
    "away_strength",
]


TARGET = "result"

MIN_TRAIN_ROWS = 80


def create_pipeline():

    preprocessor = (
        ColumnTransformer(
            transformers=[
                (
                    "numeric",
                    StandardScaler(),
                    NUMERIC_FEATURES,
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


def evaluate_league(
    league_data,
):

    months = sorted(
        league_data[
            "month"
        ].unique()
    )

    all_actual = []
    all_predictions = []

    all_probabilities = []

    balanced_scores = []
    losses = []

    valid_folds = 0


    for test_month in months:

        train_data = (
            league_data[
                league_data["month"]
                < test_month
            ]
        )

        test_data = (
            league_data[
                league_data["month"]
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
                NUMERIC_FEATURES
            ]
        )

        y_train = (
            train_data[
                TARGET
            ]
        )


        X_test = (
            test_data[
                NUMERIC_FEATURES
            ]
        )

        y_test = (
            test_data[
                TARGET
            ]
        )


        pipeline = (
            create_pipeline()
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


        all_actual.extend(
            y_test.tolist()
        )


        all_predictions.extend(
            predictions.tolist()
        )


        all_probabilities.extend(
            probabilities.tolist()
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


        valid_folds += 1


    if not all_actual:
        return None


    accuracy = (
        accuracy_score(
            all_actual,
            all_predictions,
        )
    )


    balanced = (
        sum(
            balanced_scores
        )
        / len(
            balanced_scores
        )
    )


    loss = (
        sum(
            losses
        )
        / len(
            losses
        )
    )


    return {
        "matches":
            len(
                all_actual
            ),

        "folds":
            valid_folds,

        "accuracy":
            accuracy,

        "balanced":
            balanced,

        "log_loss":
            loss,
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
        .dt.tz_convert(
            None
        )
        .dt.to_period(
            "M"
        )
    )


    print()
    print("=" * 85)
    print(
        "ANALITIKO PER-LEAGUE MODEL VALIDATION"
    )
    print("=" * 85)


    results = []


    for league in sorted(
        data[
            "league"
        ].unique()
    ):

        league_data = (
            data[
                data["league"]
                == league
            ]
            .copy()
        )


        print()
        print(
            f"Evaluating: "
            f"{league}"
        )

        print(
            f"Rows: "
            f"{len(league_data)}"
        )


        result = (
            evaluate_league(
                league_data
            )
        )


        if result is None:

            print(
                "Not enough data."
            )

            continue


        result[
            "league"
        ] = league


        results.append(
            result
        )


        print(
            f"Matches tested: "
            f"{result['matches']}"
        )

        print(
            f"Folds: "
            f"{result['folds']}"
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
        key=lambda item:
            item["accuracy"],
        reverse=True,
    )


    print()
    print("=" * 85)
    print("FINAL RANKING")
    print("=" * 85)

    print()

    print(
        f"{'League':<25}"
        f"{'Tested':>10}"
        f"{'Folds':>8}"
        f"{'Accuracy':>12}"
        f"{'Balanced':>12}"
        f"{'LogLoss':>12}"
    )


    for result in results:

        print(
            f"{result['league']:<25}"
            f"{result['matches']:>10}"
            f"{result['folds']:>8}"
            f"{result['accuracy'] * 100:>11.1f}%"
            f"{result['balanced'] * 100:>11.1f}%"
            f"{result['log_loss']:>12.4f}"
        )


    print()
    print("=" * 85)


if __name__ == "__main__":
    run()