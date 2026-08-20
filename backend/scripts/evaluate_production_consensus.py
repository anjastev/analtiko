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

from app.predictions.engine import (
    calculate_match_prediction,
)


DATA_FILE = Path(
    "data/analitiko_dataset.csv"
)

TARGET = "result"

MIN_TRAIN_ROWS = 200


# ============================================================
# ML FEATURES
# BASE + DIFF
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


LEAGUE_THRESHOLDS = {
    "Bundesliga": 48.0,
    "La Liga": 50.0,
    "Premier League": 48.0,
    "Serie A": 48.0,
}


DEFAULT_THRESHOLD = 50.0


# ============================================================
# ML PIPELINE
# ============================================================

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


# ============================================================
# ANALITIKO SCORE
# ============================================================

def calculate_analitiko_scores(
    probabilities,
):

    sorted_probabilities = (
        np.sort(
            probabilities,
            axis=1,
        )
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
# ACCURACY
# ============================================================

def accuracy(
    actual,
    predicted,
):

    if len(actual) == 0:
        return None


    return float(
        np.mean(
            np.asarray(actual)
            ==
            np.asarray(predicted)
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
# PRODUCTION RULE ENGINE
# ============================================================

def get_rule_prediction(
    row,
):

    prediction = (
        calculate_match_prediction(
            home_form=
                float(
                    row[
                        "home_form"
                    ]
                ),

            away_form=
                float(
                    row[
                        "away_form"
                    ]
                ),

            home_goals=
                float(
                    row[
                        "home_goals_avg"
                    ]
                ),

            away_goals=
                float(
                    row[
                        "away_goals_avg"
                    ]
                ),

            home_xg=
                float(
                    row[
                        "home_xg"
                    ]
                ),

            away_xg=
                float(
                    row[
                        "away_xg"
                    ]
                ),

            home_odds=
                float(
                    row[
                        "home_odds"
                    ]
                ),

            draw_odds=
                float(
                    row[
                        "draw_odds"
                    ]
                ),

            away_odds=
                float(
                    row[
                        "away_odds"
                    ]
                ),

            home_h2h_score=
                float(
                    row[
                        "h2h_home_score"
                    ]
                ),

            away_h2h_score=
                float(
                    row[
                        "h2h_away_score"
                    ]
                ),
        )
    )


    return (
        str(
            prediction[
                "main_pick"
            ]
        )
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


    print()
    print("=" * 82)
    print(
        "ANALITIKO PRODUCTION CONSENSUS VALIDATION"
    )
    print("=" * 82)

    print(
        f"Dataset rows: "
        f"{len(data)}"
    )


    # ========================================================
    # REQUIRE HISTORICAL ODDS
    # ========================================================

    required_columns = (
        NUMERIC_FEATURES
        +
        CATEGORICAL_FEATURES
        +
        [
            TARGET,
            "match_date",
            "home_odds",
            "draw_odds",
            "away_odds",
            "has_odds",
        ]
    )


    missing_columns = [
        column
        for column in required_columns
        if column
        not in data.columns
    ]


    if missing_columns:

        print()
        print(
            "Missing columns:"
        )

        for column in missing_columns:

            print(
                f"- {column}"
            )

        return


    # ========================================================
    # DATE
    # ========================================================

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
        .sort_values(
            "match_date"
        )
        .reset_index(
            drop=True
        )
    )


    # ========================================================
    # ONLY ROWS WITH REAL ODDS
    # ========================================================

    before_odds_filter = (
        len(data)
    )


    data = (
        data[
            (
                data[
                    "has_odds"
                ]
                == True
            )
            &
            (
                data[
                    "home_odds"
                ]
                .notna()
            )
            &
            (
                data[
                    "draw_odds"
                ]
                .notna()
            )
            &
            (
                data[
                    "away_odds"
                ]
                .notna()
            )
        ]
        .copy()
    )


    print(
        f"Rows with historical odds: "
        f"{len(data)} / "
        f"{before_odds_filter}"
    )


    if len(data) == 0:

        print(
            "No historical odds available."
        )

        return


    data[
        "month"
    ] = (
        data[
            "match_date"
        ]
        .dt
        .tz_convert(None)
        .dt
        .to_period("M")
    )


    feature_columns = (
        NUMERIC_FEATURES
        +
        CATEGORICAL_FEATURES
    )


    months = sorted(
        data[
            "month"
        ]
        .unique()
    )


    records = []


    # ========================================================
    # WALK-FORWARD
    # ========================================================

    for test_month in months:

        train_data = (
            data[
                data[
                    "month"
                ]
                < test_month
            ]
        )


        test_data = (
            data[
                data[
                    "month"
                ]
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


        ml_probabilities = (
            pipeline.predict_proba(
                test_data[
                    feature_columns
                ]
            )
        )


        ml_scores = (
            calculate_analitiko_scores(
                ml_probabilities
            )
        )


        for position, (
            _,
            row,
        ) in enumerate(
            test_data.iterrows()
        ):

            try:

                rule_pick = (
                    get_rule_prediction(
                        row
                    )
                )


            except Exception as error:

                print(
                    "Rule engine failed for "
                    f"match_id="
                    f"{row.get('match_id')}: "
                    f"{error}"
                )

                continue


            ml_pick = (
                str(
                    ml_predictions[
                        position
                    ]
                )
            )


            actual = (
                str(
                    row[
                        TARGET
                    ]
                )
            )


            league = (
                str(
                    row[
                        "league"
                    ]
                )
            )


            ml_score = (
                float(
                    ml_scores[
                        position
                    ]
                )
            )


            threshold = (
                LEAGUE_THRESHOLDS.get(
                    league,
                    DEFAULT_THRESHOLD,
                )
            )


            ml_strong = (
                ml_score
                >= threshold
            )


            agreement = (
                rule_pick
                == ml_pick
            )


            records.append(
                {
                    "match_id":
                        row.get(
                            "match_id"
                        ),

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
                        ml_score,

                    "threshold":
                        threshold,

                    "ml_strong":
                        ml_strong,

                    "agreement":
                        agreement,
                }
            )


    if not records:

        print()
        print(
            "No valid walk-forward "
            "predictions produced."
        )

        return


    results = (
        pd.DataFrame(
            records
        )
    )


    total = (
        len(
            results
        )
    )


    # ========================================================
    # BASIC ACCURACY
    # ========================================================

    ml_accuracy = (
        accuracy(
            results[
                "actual"
            ],
            results[
                "ml_pick"
            ],
        )
    )


    rule_accuracy = (
        accuracy(
            results[
                "actual"
            ],
            results[
                "rule_pick"
            ],
        )
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


    agreement_accuracy = (
        accuracy(
            agreement[
                "actual"
            ],
            agreement[
                "ml_pick"
            ],
        )
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


    disagreement_rule_accuracy = (
        accuracy(
            disagreement[
                "actual"
            ],
            disagreement[
                "rule_pick"
            ],
        )
    )


    # ========================================================
    # STRONG ML
    # ========================================================

    strong = (
        results[
            results[
                "ml_strong"
            ]
        ]
    )


    strong_accuracy = (
        accuracy(
            strong[
                "actual"
            ],
            strong[
                "ml_pick"
            ],
        )
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


    # ========================================================
    # SUMMARY
    # ========================================================

    print()
    print("=" * 82)
    print(
        "OVERALL"
    )
    print("=" * 82)

    print(
        f"Walk-forward matches: "
        f"{total}"
    )

    print(
        f"ML accuracy: "
        f"{format_accuracy(ml_accuracy)}"
    )

    print(
        f"Production Rule accuracy: "
        f"{format_accuracy(rule_accuracy)}"
    )


    print()
    print("=" * 82)
    print(
        "PRODUCTION RULE + ML AGREEMENT"
    )
    print("=" * 82)

    print(
        f"Matches: "
        f"{len(agreement)}"
    )

    print(
        f"Coverage: "
        f"{len(agreement) / total * 100:.1f}%"
    )

    print(
        f"Accuracy: "
        f"{format_accuracy(agreement_accuracy)}"
    )


    print()
    print("=" * 82)
    print(
        "DISAGREEMENT"
    )
    print("=" * 82)

    print(
        f"Matches: "
        f"{len(disagreement)}"
    )

    print(
        f"Coverage: "
        f"{len(disagreement) / total * 100:.1f}%"
    )

    print(
        f"ML accuracy: "
        f"{format_accuracy(disagreement_ml_accuracy)}"
    )

    print(
        f"Rule accuracy: "
        f"{format_accuracy(disagreement_rule_accuracy)}"
    )


    print()
    print("=" * 82)
    print(
        "ML STRONG"
    )
    print("=" * 82)

    print(
        f"Matches: "
        f"{len(strong)}"
    )

    print(
        f"Coverage: "
        f"{len(strong) / total * 100:.1f}%"
    )

    print(
        f"Accuracy: "
        f"{format_accuracy(strong_accuracy)}"
    )


    print()
    print("=" * 82)
    print(
        "PRODUCTION CONSENSUS + ML STRONG"
    )
    print("=" * 82)

    print(
        f"Matches: "
        f"{len(consensus_strong)}"
    )

    print(
        f"Coverage: "
        f"{len(consensus_strong) / total * 100:.1f}%"
    )

    print(
        f"Accuracy: "
        f"{format_accuracy(consensus_strong_accuracy)}"
    )


    # ========================================================
    # LEAGUES
    # ========================================================

    print()
    print("=" * 82)
    print(
        "BY LEAGUE"
    )
    print("=" * 82)

    print()

    print(
        f"{'League':<24}"
        f"{'Test':>8}"
        f"{'Agree':>8}"
        f"{'AgreeAcc':>12}"
        f"{'Strong':>10}"
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


        agree_acc = (
            accuracy(
                league_agreement[
                    "actual"
                ],
                league_agreement[
                    "ml_pick"
                ],
            )
        )


        strong_acc = (
            accuracy(
                league_consensus_strong[
                    "actual"
                ],
                league_consensus_strong[
                    "ml_pick"
                ],
            )
        )


        print(
            f"{league:<24}"
            f"{len(league_data):>8}"
            f"{len(league_agreement):>8}"
            f"{format_accuracy(agree_acc):>12}"
            f"{len(league_consensus_strong):>10}"
            f"{format_accuracy(strong_acc):>12}"
        )


    # ========================================================
    # CONSENSUS SCORE BUCKETS
    # ========================================================

    print()
    print("=" * 82)
    print(
        "CONSENSUS BY ML SCORE"
    )
    print("=" * 82)

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
    print("=" * 82)
    print(
        "PRODUCTION CONSENSUS VALIDATION COMPLETE"
    )
    print("=" * 82)


if __name__ == "__main__":
    run()