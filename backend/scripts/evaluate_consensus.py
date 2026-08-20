from pathlib import Path

import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import (
    OneHotEncoder,
    StandardScaler,
)


DATA_FILE = Path(
    "data/analitiko_dataset.csv"
)

TARGET = "result"

MIN_TRAIN_ROWS = 200


# ============================================================
# ML FEATURES
#
# Keep this aligned with the currently selected ML model.
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


# ============================================================
# VALIDATED LEAGUE THRESHOLDS
# ============================================================

LEAGUE_THRESHOLDS = {
    "Bundesliga": 48.0,
    "La Liga": 50.0,
    "Premier League": 48.0,
    "Serie A": 48.0,
}

DEFAULT_THRESHOLD = 50.0


# ============================================================
# ML MODEL
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
# RULE ENGINE
#
# Historical approximation of the current rule engine using
# leakage-safe dataset features.
#
# IMPORTANT:
# We intentionally do not use current/live odds here unless
# the dataset contains historical pre-match odds.
# ============================================================

def rule_engine_prediction(
    row,
):

    home_score = 0.0
    away_score = 0.0

    # Form
    home_score += (
        float(row["home_form"])
        * 0.35
    )

    away_score += (
        float(row["away_form"])
        * 0.35
    )


    # Goals scored
    home_score += (
        float(row["home_goals_avg"])
        * 1.25
    )

    away_score += (
        float(row["away_goals_avg"])
        * 1.25
    )


    # Defensive performance.
    # Lower conceded = better.
    home_score += (
        max(
            0.0,
            3.0
            - float(
                row[
                    "home_goals_against_avg"
                ]
            ),
        )
        * 0.65
    )

    away_score += (
        max(
            0.0,
            3.0
            - float(
                row[
                    "away_goals_against_avg"
                ]
            ),
        )
        * 0.65
    )


    # xG
    home_score += (
        float(row["home_xg"])
        * 1.10
    )

    away_score += (
        float(row["away_xg"])
        * 1.10
    )


    # H2H
    home_score += (
        float(
            row[
                "h2h_home_score"
            ]
        )
        * 0.20
    )

    away_score += (
        float(
            row[
                "h2h_away_score"
            ]
        )
        * 0.20
    )


    difference = (
        home_score
        - away_score
    )


    # Draw zone
    if abs(difference) < 0.55:
        return "DRAW"

    if difference > 0:
        return "HOME"

    return "AWAY"


# ============================================================
# ANALITIKO SCORE
# ============================================================

def calculate_analitiko_scores(
    probabilities,
):

    sorted_probabilities = np.sort(
        probabilities,
        axis=1,
    )

    top_probability = (
        sorted_probabilities[:, -1]
        * 100
    )

    second_probability = (
        sorted_probabilities[:, -2]
        * 100
    )

    margin = (
        top_probability
        - second_probability
    )

    score = (
        top_probability * 0.70
        +
        margin * 0.30
    )

    return score


# ============================================================
# ACCURACY HELPER
# ============================================================

def accuracy(
    actual,
    predicted,
):

    if len(actual) == 0:
        return None

    return float(
        np.mean(
            np.array(actual)
            ==
            np.array(predicted)
        )
    )


def format_accuracy(
    value,
):

    if value is None:
        return "-"

    return (
        f"{value * 100:.1f}%"
    )


# ============================================================
# MAIN
# ============================================================

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


    missing = [
        column
        for column in (
            feature_columns
            + [TARGET]
        )
        if column
        not in data.columns
    ]


    if missing:

        print(
            "Missing dataset columns:"
        )

        for column in missing:
            print(
                f"- {column}"
            )

        return


    print()
    print("=" * 78)
    print(
        "ANALITIKO CONSENSUS VALIDATION"
    )
    print("=" * 78)

    print(
        f"Dataset rows: "
        f"{len(data)}"
    )


    # ========================================================
    # COLLECT WALK-FORWARD PREDICTIONS
    # ========================================================

    records = []


    months = sorted(
        data[
            "month"
        ].unique()
    )


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
            .copy()
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


        ml_predictions = (
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


        ml_scores = (
            calculate_analitiko_scores(
                probabilities
            )
        )


        for position, (
            index,
            row,
        ) in enumerate(
            test_data.iterrows()
        ):

            ml_pick = str(
                ml_predictions[
                    position
                ]
            )


            rule_pick = (
                rule_engine_prediction(
                    row
                )
            )


            score = float(
                ml_scores[
                    position
                ]
            )


            league = str(
                row["league"]
            )


            threshold = (
                LEAGUE_THRESHOLDS.get(
                    league,
                    DEFAULT_THRESHOLD,
                )
            )


            is_strong = (
                score
                >= threshold
            )


            actual = str(
                row[
                    TARGET
                ]
            )


            records.append(
                {
                    "match_date":
                        row[
                            "match_date"
                        ],

                    "league":
                        league,

                    "actual":
                        actual,

                    "rule_pick":
                        rule_pick,

                    "ml_pick":
                        ml_pick,

                    "ml_score":
                        score,

                    "threshold":
                        threshold,

                    "ml_strong":
                        is_strong,

                    "agreement":
                        (
                            rule_pick
                            == ml_pick
                        ),
                }
            )


    if not records:

        print(
            "No walk-forward predictions."
        )

        return


    results = pd.DataFrame(
        records
    )


    # ========================================================
    # OVERALL
    # ========================================================

    total = len(
        results
    )


    ml_accuracy = accuracy(
        results["actual"],
        results["ml_pick"],
    )


    rule_accuracy = accuracy(
        results["actual"],
        results["rule_pick"],
    )


    # ========================================================
    # AGREEMENT
    # ========================================================

    agreement = (
        results[
            results[
                "agreement"
            ]
        ]
    )


    disagreement = (
        results[
            ~results[
                "agreement"
            ]
        ]
    )


    agreement_accuracy = accuracy(
        agreement[
            "actual"
        ],
        agreement[
            "ml_pick"
        ],
    )


    disagreement_ml_accuracy = (
        accuracy(
            disagreement[
                "actual"
            ],
            disagreement[
                "ml_pick"
            ],
        )
    )


    agreement_coverage = (
        len(agreement)
        / total
    )


    # ========================================================
    # ML STRONG
    # ========================================================

    strong = (
        results[
            results[
                "ml_strong"
            ]
        ]
    )


    strong_accuracy = accuracy(
        strong[
            "actual"
        ],
        strong[
            "ml_pick"
        ],
    )


    strong_coverage = (
        len(strong)
        / total
    )


    # ========================================================
    # CONSENSUS STRONG
    # ========================================================

    consensus_strong = (
        results[
            (
                results[
                    "agreement"
                ]
            )
            &
            (
                results[
                    "ml_strong"
                ]
            )
        ]
    )


    consensus_strong_accuracy = (
        accuracy(
            consensus_strong[
                "actual"
            ],
            consensus_strong[
                "ml_pick"
            ],
        )
    )


    consensus_strong_coverage = (
        len(
            consensus_strong
        )
        / total
    )


    # ========================================================
    # PRINT SUMMARY
    # ========================================================

    print()
    print("=" * 78)
    print(
        "OVERALL RESULTS"
    )
    print("=" * 78)

    print(
        f"Walk-forward matches: "
        f"{total}"
    )

    print()

    print(
        f"ML accuracy: "
        f"{format_accuracy(ml_accuracy)}"
    )

    print(
        f"Rule accuracy: "
        f"{format_accuracy(rule_accuracy)}"
    )


    print()
    print("=" * 78)
    print(
        "AGREEMENT"
    )
    print("=" * 78)

    print(
        f"Matches: "
        f"{len(agreement)}"
    )

    print(
        f"Coverage: "
        f"{agreement_coverage * 100:.1f}%"
    )

    print(
        f"Accuracy: "
        f"{format_accuracy(agreement_accuracy)}"
    )


    print()
    print("=" * 78)
    print(
        "DISAGREEMENT"
    )
    print("=" * 78)

    print(
        f"Matches: "
        f"{len(disagreement)}"
    )

    print(
        "ML accuracy when models disagree: "
        f"{format_accuracy(disagreement_ml_accuracy)}"
    )


    print()
    print("=" * 78)
    print(
        "ML STRONG"
    )
    print("=" * 78)

    print(
        f"Matches: "
        f"{len(strong)}"
    )

    print(
        f"Coverage: "
        f"{strong_coverage * 100:.1f}%"
    )

    print(
        f"Accuracy: "
        f"{format_accuracy(strong_accuracy)}"
    )


    print()
    print("=" * 78)
    print(
        "CONSENSUS + ML STRONG"
    )
    print("=" * 78)

    print(
        f"Matches: "
        f"{len(consensus_strong)}"
    )

    print(
        f"Coverage: "
        f"{consensus_strong_coverage * 100:.1f}%"
    )

    print(
        f"Accuracy: "
        f"{format_accuracy(consensus_strong_accuracy)}"
    )


    # ========================================================
    # BY LEAGUE
    # ========================================================

    print()
    print("=" * 78)
    print(
        "CONSENSUS BY LEAGUE"
    )
    print("=" * 78)

    print()

    print(
        f"{'League':<24}"
        f"{'Test':>8}"
        f"{'Agree':>8}"
        f"{'Coverage':>12}"
        f"{'AgreeAcc':>12}"
        f"{'Strong':>9}"
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


        league_agreement = (
            league_data[
                league_data[
                    "agreement"
                ]
            ]
        )


        league_consensus_strong = (
            league_data[
                (
                    league_data[
                        "agreement"
                    ]
                )
                &
                (
                    league_data[
                        "ml_strong"
                    ]
                )
            ]
        )


        league_agreement_accuracy = (
            accuracy(
                league_agreement[
                    "actual"
                ],
                league_agreement[
                    "ml_pick"
                ],
            )
        )


        league_strong_accuracy = (
            accuracy(
                league_consensus_strong[
                    "actual"
                ],
                league_consensus_strong[
                    "ml_pick"
                ],
            )
        )


        league_coverage = (
            len(
                league_agreement
            )
            /
            len(
                league_data
            )
            * 100
        )


        print(
            f"{league:<24}"
            f"{len(league_data):>8}"
            f"{len(league_agreement):>8}"
            f"{league_coverage:>11.1f}%"
            f"{format_accuracy(league_agreement_accuracy):>12}"
            f"{len(league_consensus_strong):>9}"
            f"{format_accuracy(league_strong_accuracy):>12}"
        )


    # ========================================================
    # SCORE BUCKETS FOR CONSENSUS
    # ========================================================

    print()
    print("=" * 78)
    print(
        "CONSENSUS BY ML SCORE"
    )
    print("=" * 78)

    print()


    buckets = [
        (
            "< 35",
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
            agreement[
                (
                    agreement[
                        "ml_score"
                    ]
                    >= lower
                )
                &
                (
                    agreement[
                        "ml_score"
                    ]
                    < upper
                )
            ]
        )


        bucket_accuracy = (
            accuracy(
                bucket[
                    "actual"
                ],
                bucket[
                    "ml_pick"
                ],
            )
        )


        print(
            f"{label:<14}"
            f"{len(bucket):>10}"
            f"{format_accuracy(bucket_accuracy):>12}"
        )


    print()
    print("=" * 78)
    print(
        "CONSENSUS VALIDATION COMPLETE"
    )
    print("=" * 78)


if __name__ == "__main__":
    run()