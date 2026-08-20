from pathlib import Path

import numpy as np
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


# ============================================================
# IMPORTANT
#
# Keep this identical to the feature set of the model that
# you currently consider your selected ML configuration.
#
# Current benchmark: BASE + DIFF
# ============================================================

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


FEATURE_COLUMNS = (
    NUMERIC_FEATURES
    + CATEGORICAL_FEATURES
)


# ============================================================
# STRICT TIME SPLIT
#
# First 80% = development period
# Last 20%  = untouched holdout
# ============================================================

HOLDOUT_FRACTION = 0.20


# ============================================================
# THRESHOLD SEARCH
#
# Threshold selection happens ONLY inside development data.
# ============================================================

THRESHOLDS = [
    30,
    32,
    34,
    35,
    36,
    38,
    40,
    42,
    45,
    48,
    50,
    52,
    55,
]


MIN_THRESHOLD_COVERAGE = 0.15

MIN_LEAGUE_SELECTED = 20


# ============================================================
# PIPELINE
# ============================================================

def create_pipeline():

    preprocessor = ColumnTransformer(
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


# ============================================================
# ANALITIKO SCORE
# ============================================================

def calculate_scores(
    probabilities,
):

    sorted_probabilities = np.sort(
        probabilities,
        axis=1,
    )


    top = (
        sorted_probabilities[:, -1]
        * 100
    )


    second = (
        sorted_probabilities[:, -2]
        * 100
    )


    margin = (
        top
        - second
    )


    return (
        top * 0.70
        +
        margin * 0.30
    )


# ============================================================
# DEVELOPMENT WALK-FORWARD PREDICTIONS
#
# Thresholds must NOT see holdout data.
# ============================================================

def build_development_predictions(
    development,
):

    development = (
        development
        .copy()
        .sort_values(
            "match_date"
        )
        .reset_index(
            drop=True
        )
    )


    development["month"] = (
        development[
            "match_date"
        ]
        .dt
        .tz_convert(None)
        .dt
        .to_period("M")
    )


    months = sorted(
        development[
            "month"
        ].unique()
    )


    records = []


    for test_month in months:

        train = (
            development[
                development[
                    "month"
                ]
                < test_month
            ]
        )


        test = (
            development[
                development[
                    "month"
                ]
                == test_month
            ]
        )


        # Need a meaningful amount of
        # historical training data.

        if len(train) < 150:
            continue


        if len(test) == 0:
            continue


        if (
            train[
                TARGET
            ].nunique()
            < 3
        ):
            continue


        model = (
            create_pipeline()
        )


        model.fit(
            train[
                FEATURE_COLUMNS
            ],
            train[
                TARGET
            ],
        )


        predictions = (
            model.predict(
                test[
                    FEATURE_COLUMNS
                ]
            )
        )


        probabilities = (
            model.predict_proba(
                test[
                    FEATURE_COLUMNS
                ]
            )
        )


        scores = (
            calculate_scores(
                probabilities
            )
        )


        for position, (
            _,
            row,
        ) in enumerate(
            test.iterrows()
        ):

            records.append(
                {
                    "league":
                        str(
                            row[
                                "league"
                            ]
                        ),

                    "actual":
                        str(
                            row[
                                TARGET
                            ]
                        ),

                    "prediction":
                        str(
                            predictions[
                                position
                            ]
                        ),

                    "score":
                        float(
                            scores[
                                position
                            ]
                        ),
                }
            )


    return pd.DataFrame(
        records
    )


# ============================================================
# SELECT THRESHOLDS
#
# This sees DEVELOPMENT predictions only.
# ============================================================

def select_thresholds(
    development_predictions,
):

    selected = {}


    leagues = sorted(
        development_predictions[
            "league"
        ].unique()
    )


    print()
    print("=" * 80)
    print(
        "THRESHOLD SELECTION - DEVELOPMENT ONLY"
    )
    print("=" * 80)


    for league in leagues:

        league_data = (
            development_predictions[
                development_predictions[
                    "league"
                ]
                == league
            ]
        )


        total = (
            len(
                league_data
            )
        )


        print()
        print(
            f"{league}"
        )

        print(
            f"Development predictions: "
            f"{total}"
        )


        best = None


        for threshold in THRESHOLDS:

            mask = (
                league_data[
                    "score"
                ]
                >= threshold
            )


            subset = (
                league_data[
                    mask
                ]
            )


            count = (
                len(
                    subset
                )
            )


            if count == 0:
                continue


            coverage = (
                count
                / total
            )


            accuracy = (
                subset[
                    "prediction"
                ]
                ==
                subset[
                    "actual"
                ]
            ).mean()


            if (
                coverage
                < MIN_THRESHOLD_COVERAGE
            ):
                continue


            if (
                count
                < MIN_LEAGUE_SELECTED
            ):
                continue


            print(
                f"  >= {threshold:<2} | "
                f"{count:>4} picks | "
                f"coverage "
                f"{coverage * 100:>5.1f}% | "
                f"accuracy "
                f"{accuracy * 100:>5.1f}%"
            )


            candidate = {
                "threshold":
                    float(
                        threshold
                    ),

                "accuracy":
                    float(
                        accuracy
                    ),

                "coverage":
                    float(
                        coverage
                    ),

                "selected":
                    count,
            }


            if best is None:

                best = candidate

            elif (
                candidate[
                    "accuracy"
                ]
                >
                best[
                    "accuracy"
                ]
            ):

                best = candidate

            elif (
                candidate[
                    "accuracy"
                ]
                ==
                best[
                    "accuracy"
                ]
                and
                candidate[
                    "coverage"
                ]
                >
                best[
                    "coverage"
                ]
            ):

                best = candidate


        if best is None:

            # Conservative fallback.

            selected[
                league
            ] = 50.0


            print(
                "  No eligible threshold."
            )

            print(
                "  Fallback threshold: 50"
            )


        else:

            selected[
                league
            ] = (
                best[
                    "threshold"
                ]
            )


            print(
                "  SELECTED: "
                f"{best['threshold']:.0f}"
            )

            print(
                "  Development accuracy: "
                f"{best['accuracy'] * 100:.1f}%"
            )

            print(
                "  Development coverage: "
                f"{best['coverage'] * 100:.1f}%"
            )


    return selected


# ============================================================
# HOLDOUT TEST
#
# One final model is trained on ALL development data.
#
# Thresholds are already frozen before this function receives
# holdout labels.
# ============================================================

def evaluate_holdout(
    development,
    holdout,
    thresholds,
):

    model = (
        create_pipeline()
    )


    model.fit(
        development[
            FEATURE_COLUMNS
        ],
        development[
            TARGET
        ],
    )


    predictions = (
        model.predict(
            holdout[
                FEATURE_COLUMNS
            ]
        )
    )


    probabilities = (
        model.predict_proba(
            holdout[
                FEATURE_COLUMNS
            ]
        )
    )


    classes = (
        model
        .named_steps[
            "model"
        ]
        .classes_
    )


    scores = (
        calculate_scores(
            probabilities
        )
    )


    results = (
        holdout[
            [
                "match_id",
                "match_date",
                "league",
                TARGET,
            ]
        ]
        .copy()
        .reset_index(
            drop=True
        )
    )


    results[
        "prediction"
    ] = predictions


    results[
        "score"
    ] = scores


    results[
        "threshold"
    ] = (
        results[
            "league"
        ]
        .map(
            thresholds
        )
        .fillna(
            50.0
        )
    )


    results[
        "strong"
    ] = (
        results[
            "score"
        ]
        >=
        results[
            "threshold"
        ]
    )


    # ========================================================
    # OVERALL METRICS
    # ========================================================

    overall_accuracy = (
        accuracy_score(
            results[
                TARGET
            ],
            results[
                "prediction"
            ],
        )
    )


    balanced = (
        balanced_accuracy_score(
            results[
                TARGET
            ],
            results[
                "prediction"
            ],
        )
    )


    loss = (
        log_loss(
            results[
                TARGET
            ],
            probabilities,
            labels=
                classes,
        )
    )


    # ========================================================
    # HOME BASELINE
    # ========================================================

    home_predictions = (
        np.array(
            ["HOME"]
            * len(
                results
            )
        )
    )


    home_baseline = (
        accuracy_score(
            results[
                TARGET
            ],
            home_predictions,
        )
    )


    # ========================================================
    # MAJORITY CLASS BASELINE
    #
    # Chosen using DEVELOPMENT ONLY.
    # ========================================================

    majority_class = (
        development[
            TARGET
        ]
        .value_counts()
        .idxmax()
    )


    majority_predictions = (
        np.array(
            [
                majority_class
            ]
            * len(
                results
            )
        )
    )


    majority_accuracy = (
        accuracy_score(
            results[
                TARGET
            ],
            majority_predictions,
        )
    )


    # ========================================================
    # STRONG
    # ========================================================

    strong = (
        results[
            results[
                "strong"
            ]
        ]
    )


    if len(strong) > 0:

        strong_accuracy = (
            accuracy_score(
                strong[
                    TARGET
                ],
                strong[
                    "prediction"
                ],
            )
        )

    else:

        strong_accuracy = None


    strong_coverage = (
        len(
            strong
        )
        / len(
            results
        )
    )


    # ========================================================
    # PRINT
    # ========================================================

    print()
    print("=" * 80)
    print(
        "STRICT UNTOUCHED HOLDOUT RESULTS"
    )
    print("=" * 80)


    print(
        f"Holdout matches: "
        f"{len(results)}"
    )


    print()
    print(
        f"ML accuracy: "
        f"{overall_accuracy * 100:.1f}%"
    )

    print(
        f"Balanced accuracy: "
        f"{balanced * 100:.1f}%"
    )

    print(
        f"Log loss: "
        f"{loss:.4f}"
    )


    print()
    print(
        f"Always HOME baseline: "
        f"{home_baseline * 100:.1f}%"
    )

    print(
        f"Development majority class: "
        f"{majority_class}"
    )

    print(
        f"Majority baseline: "
        f"{majority_accuracy * 100:.1f}%"
    )


    print()
    print(
        "STRONG PICKS"
    )

    print(
        f"Selected: "
        f"{len(strong)}"
    )

    print(
        f"Coverage: "
        f"{strong_coverage * 100:.1f}%"
    )

    print(
        "Accuracy: "
        + (
            f"{strong_accuracy * 100:.1f}%"
            if strong_accuracy
            is not None
            else "-"
        )
    )


    # ========================================================
    # BY LEAGUE
    # ========================================================

    print()
    print("=" * 80)
    print(
        "HOLDOUT BY LEAGUE"
    )
    print("=" * 80)

    print()

    print(
        f"{'League':<24}"
        f"{'Test':>8}"
        f"{'Acc':>10}"
        f"{'Threshold':>12}"
        f"{'Strong':>10}"
        f"{'Coverage':>12}"
        f"{'StrongAcc':>12}"
    )


    for league in sorted(
        results[
            "league"
        ].unique()
    ):

        league_data = (
            results[
                results[
                    "league"
                ]
                == league
            ]
        )


        league_accuracy = (
            accuracy_score(
                league_data[
                    TARGET
                ],
                league_data[
                    "prediction"
                ],
            )
        )


        league_strong = (
            league_data[
                league_data[
                    "strong"
                ]
            ]
        )


        if (
            len(
                league_strong
            )
            > 0
        ):

            league_strong_accuracy = (
                accuracy_score(
                    league_strong[
                        TARGET
                    ],
                    league_strong[
                        "prediction"
                    ],
                )
            )

            strong_text = (
                f"{league_strong_accuracy * 100:.1f}%"
            )

        else:

            strong_text = "-"


        coverage = (
            len(
                league_strong
            )
            /
            len(
                league_data
            )
            * 100
        )


        threshold = (
            thresholds.get(
                league,
                50.0,
            )
        )


        print(
            f"{league:<24}"
            f"{len(league_data):>8}"
            f"{league_accuracy * 100:>9.1f}%"
            f"{threshold:>12.1f}"
            f"{len(league_strong):>10}"
            f"{coverage:>11.1f}%"
            f"{strong_text:>12}"
        )


    # ========================================================
    # SCORE BUCKETS
    # ========================================================

    print()
    print("=" * 80)
    print(
        "HOLDOUT BY ANALITIKO SCORE"
    )
    print("=" * 80)

    print()


    buckets = [
        (
            "<35",
            0,
            35,
        ),
        (
            "35-39.9",
            35,
            40,
        ),
        (
            "40-44.9",
            40,
            45,
        ),
        (
            "45-49.9",
            45,
            50,
        ),
        (
            "50+",
            50,
            101,
        ),
    ]


    print(
        f"{'Score':<14}"
        f"{'Matches':>10}"
        f"{'Accuracy':>12}"
    )


    for (
        label,
        lower,
        upper,
    ) in buckets:

        bucket = (
            results[
                (
                    results[
                        "score"
                    ]
                    >= lower
                )
                &
                (
                    results[
                        "score"
                    ]
                    < upper
                )
            ]
        )


        if len(bucket) > 0:

            bucket_accuracy = (
                accuracy_score(
                    bucket[
                        TARGET
                    ],
                    bucket[
                        "prediction"
                    ],
                )
            )

            accuracy_text = (
                f"{bucket_accuracy * 100:.1f}%"
            )

        else:

            accuracy_text = "-"


        print(
            f"{label:<14}"
            f"{len(bucket):>10}"
            f"{accuracy_text:>12}"
        )


    return results


# ============================================================
# MAIN
# ============================================================

def run():

    if not DATA_FILE.exists():

        print(
            "Dataset not found."
        )

        return


    data = (
        pd.read_csv(
            DATA_FILE
        )
    )


    required_columns = (
        FEATURE_COLUMNS
        +
        [
            "match_id",
            "match_date",
            TARGET,
        ]
    )


    missing = [
        column
        for column
        in required_columns
        if column
        not in data.columns
    ]


    if missing:

        print(
            "Missing columns:"
        )

        for column in missing:

            print(
                f"- {column}"
            )

        return


    data[
        "match_date"
    ] = (
        pd.to_datetime(
            data[
                "match_date"
            ],
            utc=True,
        )
    )


    data = (
        data
        .dropna(
            subset=
                required_columns
        )
        .sort_values(
            "match_date"
        )
        .reset_index(
            drop=True
        )
    )


    total = (
        len(
            data
        )
    )


    split_index = int(
        total
        * (
            1
            - HOLDOUT_FRACTION
        )
    )


    development = (
        data.iloc[
            :split_index
        ]
        .copy()
    )


    holdout = (
        data.iloc[
            split_index:
        ]
        .copy()
    )


    print()
    print("=" * 80)
    print(
        "ANALITIKO STRICT OUT-OF-SAMPLE VALIDATION"
    )
    print("=" * 80)


    print(
        f"Dataset rows: "
        f"{total}"
    )


    print()
    print(
        f"Development rows: "
        f"{len(development)}"
    )

    print(
        f"Holdout rows: "
        f"{len(holdout)}"
    )


    print()
    print(
        "Development period:"
    )

    print(
        development[
            "match_date"
        ].min()
    )

    print(
        "->"
    )

    print(
        development[
            "match_date"
        ].max()
    )


    print()
    print(
        "UNTOUCHED holdout period:"
    )

    print(
        holdout[
            "match_date"
        ].min()
    )

    print(
        "->"
    )

    print(
        holdout[
            "match_date"
        ].max()
    )


    # ========================================================
    # THRESHOLD DEVELOPMENT
    # ========================================================

    development_predictions = (
        build_development_predictions(
            development
        )
    )


    print()
    print(
        "Development walk-forward "
        f"predictions: "
        f"{len(development_predictions)}"
    )


    if (
        len(
            development_predictions
        )
        == 0
    ):

        print(
            "Could not create development "
            "walk-forward predictions."
        )

        return


    thresholds = (
        select_thresholds(
            development_predictions
        )
    )


    # ========================================================
    # FREEZE
    # ========================================================

    print()
    print("=" * 80)
    print(
        "FROZEN THRESHOLDS"
    )
    print("=" * 80)


    for (
        league,
        threshold,
    ) in sorted(
        thresholds.items()
    ):

        print(
            f"{league:<25}"
            f"{threshold:.1f}"
        )


    print()
    print(
        "Threshold selection is now finished."
    )

    print(
        "The holdout labels have not been used "
        "to choose these thresholds."
    )


    # ========================================================
    # FINAL TEST
    # ========================================================

    evaluate_holdout(
        development=
            development,

        holdout=
            holdout,

        thresholds=
            thresholds,
    )


    print()
    print("=" * 80)
    print(
        "STRICT OOS VALIDATION COMPLETE"
    )
    print("=" * 80)


if __name__ == "__main__":
    run()