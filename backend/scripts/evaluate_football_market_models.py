from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from sklearn.metrics import (
    accuracy_score,
    brier_score_loss,
    log_loss,
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

MODELS_DIR = (
    BASE_DIR
    / "models"
)


FEATURES = [
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
    "league",
]


MODELS = {
    "OU_25": {
        "target": "over_25",
        "file": (
            MODELS_DIR
            / "over25_model.joblib"
        ),
    },
    "BTTS": {
        "target": "btts",
        "file": (
            MODELS_DIR
            / "btts_model.joblib"
        ),
    },
}


# Same frozen historical cutoff principle.
HOLDOUT_START = pd.Timestamp(
    "2025-04-07"
)


def print_bucket_report(
    probabilities,
    y_true,
):

    buckets = [
        (50, 55),
        (55, 60),
        (60, 65),
        (65, 70),
        (70, 75),
        (75, 80),
        (80, 85),
        (85, 101),
    ]

    print()
    print(
        "HIGH-CONFIDENCE BUCKETS"
    )

    for low, high in buckets:

        mask = (
            (probabilities >= low)
            &
            (probabilities < high)
        )

        count = int(
            mask.sum()
        )

        if count == 0:
            continue

        bucket_probs = (
            probabilities[
                mask
            ]
        )

        bucket_true = (
            y_true[
                mask
            ]
        )

        predicted_class = (
            bucket_probs >= 50.0
        ).astype(int)

        actual_class = (
            bucket_true
        )

        accuracy = (
            accuracy_score(
                actual_class,
                predicted_class,
            )
            * 100.0
        )

        print(
            f"{low:>2}-{high - 0.1:>4.1f}% "
            f"| n={count:<4} "
            f"| avg_conf="
            f"{bucket_probs.mean():.1f}% "
            f"| acc="
            f"{accuracy:.1f}%"
        )


def evaluate_model(
    name: str,
    target: str,
    model_file: Path,
    df: pd.DataFrame,
):

    print()
    print("=" * 80)
    print(
        f"MODEL: {name}"
    )
    print("=" * 80)

    if not model_file.exists():

        print(
            f"Model missing: "
            f"{model_file}"
        )

        return

    model_df = (
        df[
            FEATURES
            + [
                "match_date",
                target,
            ]
        ]
        .dropna()
        .copy()
    )

    model_df[
        "match_date"
    ] = pd.to_datetime(
        model_df[
            "match_date"
        ]
    )

    holdout = (
        model_df[
            model_df[
                "match_date"
            ]
            >= HOLDOUT_START
        ]
        .copy()
    )

    if holdout.empty:

        print(
            "No holdout rows."
        )

        return

    model = joblib.load(
        model_file
    )

    X = holdout[
        FEATURES
    ]

    y = (
        holdout[
            target
        ]
        .astype(int)
        .to_numpy()
    )

    probabilities = (
        model.predict_proba(
            X
        )
    )

    classes = list(
        model
        .named_steps["model"]
        .classes_
    )

    if 1 not in classes:

        print(
            "Positive class 1 "
            "not found."
        )

        return

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

    accuracy = (
        accuracy_score(
            y,
            predictions,
        )
        * 100.0
    )

    ll = log_loss(
        y,
        probabilities,
        labels=classes,
    )

    brier = (
        brier_score_loss(
            y,
            p_positive,
        )
    )

    print(
        f"Holdout rows: "
        f"{len(holdout)}"
    )

    print(
        f"Positive rate: "
        f"{y.mean() * 100:.1f}%"
    )

    print(
        f"Accuracy: "
        f"{accuracy:.1f}%"
    )

    print(
        f"Log loss: "
        f"{ll:.4f}"
    )

    print(
        f"Brier: "
        f"{brier:.4f}"
    )

    # ========================================================
    # PICK CONFIDENCE
    #
    # For a binary prediction:
    # confidence = max(P(YES), P(NO))
    # ========================================================

    confidence = (
        np.maximum(
            p_positive,
            1.0 - p_positive,
        )
        * 100.0
    )

    predicted_labels = (
        p_positive >= 0.5
    ).astype(int)

    correct = (
        predicted_labels == y
    )

    print()
    print(
        "CONFIDENCE THRESHOLDS"
    )

    for threshold in [
        55,
        60,
        65,
        70,
        75,
        80,
        85,
    ]:

        mask = (
            confidence
            >= threshold
        )

        count = int(
            mask.sum()
        )

        if count == 0:

            print(
                f">= {threshold}% "
                f"| n=0"
            )

            continue

        coverage = (
            count
            / len(y)
            * 100.0
        )

        accuracy_at_threshold = (
            correct[
                mask
            ].mean()
            * 100.0
        )

        average_confidence = (
            confidence[
                mask
            ].mean()
        )

        print(
            f">= {threshold}% "
            f"| n={count:<4} "
            f"| coverage="
            f"{coverage:>5.1f}% "
            f"| avg_conf="
            f"{average_confidence:>5.1f}% "
            f"| accuracy="
            f"{accuracy_at_threshold:>5.1f}%"
        )

    # ========================================================
    # CONFIDENCE BUCKETS
    # ========================================================

    print()
    print(
        "CONFIDENCE BUCKETS"
    )

    buckets = [
        (50, 55),
        (55, 60),
        (60, 65),
        (65, 70),
        (70, 75),
        (75, 80),
        (80, 85),
        (85, 101),
    ]

    for low, high in buckets:

        mask = (
            (confidence >= low)
            &
            (confidence < high)
        )

        count = int(
            mask.sum()
        )

        if count == 0:
            continue

        bucket_accuracy = (
            correct[
                mask
            ].mean()
            * 100.0
        )

        print(
            f"{low:>2}-"
            f"{high - 0.1:>4.1f}% "
            f"| n={count:<4} "
            f"| avg_conf="
            f"{confidence[mask].mean():>5.1f}% "
            f"| accuracy="
            f"{bucket_accuracy:>5.1f}%"
        )


def run():

    if not DATASET_FILE.exists():

        raise FileNotFoundError(
            f"Dataset not found: "
            f"{DATASET_FILE}"
        )

    df = pd.read_csv(
        DATASET_FILE
    )

    print()
    print("=" * 80)
    print(
        "ANALITIKO FOOTBALL MARKET VALIDATION"
    )
    print("=" * 80)

    print(
        f"Dataset rows: "
        f"{len(df)}"
    )

    print(
        f"Holdout start: "
        f"{HOLDOUT_START.date()}"
    )

    for name, config in (
        MODELS.items()
    ):

        evaluate_model(
            name=name,
            target=(
                config[
                    "target"
                ]
            ),
            model_file=(
                config[
                    "file"
                ]
            ),
            df=df,
        )

    print()
    print("=" * 80)
    print(
        "VALIDATION COMPLETE"
    )
    print("=" * 80)


if __name__ == "__main__":
    run()