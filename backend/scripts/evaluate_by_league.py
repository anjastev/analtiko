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

    # BASE + DIFF
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

MIN_TRAIN_ROWS = 200


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


def run():

    if not DATA_FILE.exists():
        print("Dataset not found.")
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


    features = (
        NUMERIC_FEATURES
        + CATEGORICAL_FEATURES
    )


    months = sorted(
        data["month"].unique()
    )


    results = {}


    print()
    print("=" * 80)
    print("ANALITIKO LEAGUE VALIDATION")
    print("=" * 80)


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


        pipeline = (
            create_pipeline()
        )


        pipeline.fit(
            train_data[
                features
            ],
            train_data[
                TARGET
            ],
        )


        predictions = (
            pipeline.predict(
                test_data[
                    features
                ]
            )
        )


        probabilities = (
            pipeline.predict_proba(
                test_data[
                    features
                ]
            )
        )


        classes = (
            pipeline
            .named_steps["model"]
            .classes_
        )


        test_data = (
            test_data.copy()
        )


        test_data[
            "prediction"
        ] = predictions


        for league in (
            test_data["league"]
            .unique()
        ):

            league_mask = (
                test_data["league"]
                == league
            )


            league_data = (
                test_data[
                    league_mask
                ]
            )


            league_predictions = (
                predictions[
                    league_mask.to_numpy()
                ]
            )


            league_probabilities = (
                probabilities[
                    league_mask.to_numpy()
                ]
            )


            actual = (
                league_data[
                    TARGET
                ]
            )


            if league not in results:

                results[league] = {
                    "actual": [],
                    "predicted": [],
                    "probabilities": [],
                }


            results[
                league
            ]["actual"].extend(
                actual.tolist()
            )


            results[
                league
            ]["predicted"].extend(
                league_predictions.tolist()
            )


            results[
                league
            ]["probabilities"].extend(
                league_probabilities.tolist()
            )


    print()
    print(
        f"{'League':<25}"
        f"{'Matches':>10}"
        f"{'Accuracy':>12}"
        f"{'Balanced':>12}"
        f"{'LogLoss':>12}"
    )

    print(
        "-" * 80
    )


    ranking = []


    for (
        league,
        result,
    ) in results.items():

        actual = (
            result[
                "actual"
            ]
        )

        predicted = (
            result[
                "predicted"
            ]
        )

        probabilities = (
            result[
                "probabilities"
            ]
        )


        if len(actual) < 10:
            continue


        accuracy = (
            accuracy_score(
                actual,
                predicted,
            )
        )


        balanced = (
            balanced_accuracy_score(
                actual,
                predicted,
            )
        )


        loss = (
            log_loss(
                actual,
                probabilities,
                labels=classes,
            )
        )


        ranking.append(
            (
                league,
                len(actual),
                accuracy,
                balanced,
                loss,
            )
        )


    ranking.sort(
        key=lambda item:
            item[2],
        reverse=True,
    )


    for (
        league,
        matches,
        accuracy,
        balanced,
        loss,
    ) in ranking:

        print(
            f"{league:<25}"
            f"{matches:>10}"
            f"{accuracy * 100:>11.1f}%"
            f"{balanced * 100:>11.1f}%"
            f"{loss:>12.4f}"
        )


    print()
    print("=" * 80)


if __name__ == "__main__":
    run()