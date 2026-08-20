from pathlib import Path

import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
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


THRESHOLDS = [
    0.30,
    0.32,
    0.34,
    0.35,
    0.36,
    0.38,
    0.40,
    0.42,
    0.45,
    0.48,
    0.50,
]


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


def calculate_analitiko_scores(
    probabilities,
):

    top_probability = (
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


    margin = (
        sorted_probabilities[:, -1]
        -
        sorted_probabilities[:, -2]
    )


    score = (
        top_probability * 0.70
        +
        margin * 0.30
    )


    return score


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


    feature_columns = (
        NUMERIC_FEATURES
        + CATEGORICAL_FEATURES
    )


    months = sorted(
        data["month"]
        .unique()
    )


    league_results = {}


    print()
    print("=" * 85)
    print(
        "ANALITIKO LEAGUE CONFIDENCE TUNING"
    )
    print("=" * 85)


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


        pipeline = (
            create_pipeline()
        )


        pipeline.fit(
            train_data[
                feature_columns
            ],
            train_data[
                TARGET
            ],
        )


        predictions = (
            pipeline.predict(
                test_data[
                    feature_columns
                ]
            )
        )


        probabilities = (
            pipeline.predict_proba(
                test_data[
                    feature_columns
                ]
            )
        )


        scores = (
            calculate_analitiko_scores(
                probabilities
            )
        )


        test_data = (
            test_data
            .copy()
            .reset_index(
                drop=True
            )
        )


        for league in (
            test_data[
                "league"
            ].unique()
        ):

            mask = (
                test_data[
                    "league"
                ]
                == league
            ).to_numpy()


            league_actual = (
                test_data.loc[
                    mask,
                    TARGET,
                ]
                .to_numpy()
            )


            league_predictions = (
                predictions[
                    mask
                ]
            )


            league_scores = (
                scores[
                    mask
                ]
            )


            if league not in league_results:

                league_results[
                    league
                ] = {
                    "actual": [],
                    "predicted": [],
                    "scores": [],
                }


            league_results[
                league
            ]["actual"].extend(
                league_actual.tolist()
            )


            league_results[
                league
            ]["predicted"].extend(
                league_predictions.tolist()
            )


            league_results[
                league
            ]["scores"].extend(
                league_scores.tolist()
            )


    print()
    print("=" * 85)
    print(
        "THRESHOLD RESULTS"
    )
    print("=" * 85)


    for league in sorted(
        league_results.keys()
    ):

        result = (
            league_results[
                league
            ]
        )


        actual = (
            pd.Series(
                result[
                    "actual"
                ]
            )
            .to_numpy()
        )


        predicted = (
            pd.Series(
                result[
                    "predicted"
                ]
            )
            .to_numpy()
        )


        scores = (
            pd.Series(
                result[
                    "scores"
                ]
            )
            .to_numpy()
        )


        total = len(
            actual
        )


        if total < 30:
            continue


        print()
        print("-" * 85)

        print(
            f"{league}"
        )

        print(
            f"Total test matches: "
            f"{total}"
        )

        print()

        print(
            f"{'Threshold':<12}"
            f"{'Selected':>10}"
            f"{'Coverage':>12}"
            f"{'Accuracy':>12}"
        )


        best = None


        for threshold in THRESHOLDS:

            mask = (
                scores
                >= threshold
            )


            selected = int(
                mask.sum()
            )


            if selected == 0:
                continue


            coverage = (
                selected
                / total
                * 100
            )


            accuracy = (
                accuracy_score(
                    actual[
                        mask
                    ],
                    predicted[
                        mask
                    ],
                )
            )


            print(
                f"{threshold * 100:<11.0f}+"
                f"{selected:>10}"
                f"{coverage:>11.1f}%"
                f"{accuracy * 100:>11.1f}%"
            )


            # Require at least
            # 15% coverage so a threshold
            # is not chosen from 2-3 matches.
            if coverage >= 15:

                if (
                    best is None
                    or
                    accuracy
                    > best[
                        "accuracy"
                    ]
                ):

                    best = {
                        "threshold":
                            threshold,

                        "accuracy":
                            accuracy,

                        "coverage":
                            coverage,

                        "selected":
                            selected,
                    }


        print()

        if best:

            print(
                "BEST PRACTICAL THRESHOLD:"
            )

            print(
                f"Score >= "
                f"{best['threshold'] * 100:.0f}"
            )

            print(
                f"Accuracy: "
                f"{best['accuracy'] * 100:.1f}%"
            )

            print(
                f"Coverage: "
                f"{best['coverage']:.1f}%"
            )

            print(
                f"Selected: "
                f"{best['selected']}"
            )

        else:

            print(
                "No threshold with "
                "at least 15% coverage."
            )


    print()
    print("=" * 85)
    print(
        "TUNING COMPLETE"
    )
    print("=" * 85)


if __name__ == "__main__":
    run()