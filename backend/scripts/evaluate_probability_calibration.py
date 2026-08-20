from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from sklearn.base import clone
from sklearn.metrics import log_loss


# ============================================================
# CONFIG
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]

DATA_PATH = (
    BASE_DIR
    / "data"
    / "analitiko_dataset.csv"
)

MODEL_PATH = (
    BASE_DIR
    / "models"
    / "result_model.joblib"
)

REPORT_DIR = (
    BASE_DIR
    / "data"
    / "reports"
)


# ============================================================
# HELPERS
# ============================================================

def normalize_result(value):

    value = str(
        value
    ).upper().strip()

    mapping = {
        "H": "HOME",
        "HOME": "HOME",

        "D": "DRAW",
        "DRAW": "DRAW",

        "A": "AWAY",
        "AWAY": "AWAY",
    }

    return mapping.get(
        value,
        value,
    )


def multiclass_brier_score(
    y_true,
    probabilities,
    classes,
):

    class_to_index = {
        cls: index
        for index, cls
        in enumerate(classes)
    }

    actual = np.zeros_like(
        probabilities,
        dtype=float,
    )

    for row_index, result in enumerate(
        y_true
    ):

        class_index = (
            class_to_index[result]
        )

        actual[
            row_index,
            class_index
        ] = 1.0

    squared_error = (
        probabilities
        - actual
    ) ** 2

    return float(
        np.mean(
            np.sum(
                squared_error,
                axis=1,
            )
        )
    )


# ============================================================
# MAIN
# ============================================================

def run():

    print()
    print("=" * 80)
    print(
        "ANALITIKO STRICT PROBABILITY CALIBRATION"
    )
    print("=" * 80)

    if not DATA_PATH.exists():

        raise FileNotFoundError(
            f"Dataset not found: {DATA_PATH}"
        )

    if not MODEL_PATH.exists():

        raise FileNotFoundError(
            f"Model not found: {MODEL_PATH}"
        )

    # ========================================================
    # LOAD
    # ========================================================

    df = pd.read_csv(
        DATA_PATH
    )

    model_template = joblib.load(
        MODEL_PATH
    )

    print(
        f"Dataset: {DATA_PATH}"
    )

    print(
        f"Rows: {len(df)}"
    )

    print(
        f"Model: {MODEL_PATH}"
    )

    # ========================================================
    # GET EXACT MODEL FEATURES
    # ========================================================

    if not hasattr(
        model_template,
        "feature_names_in_",
    ):

        raise ValueError(
            "Model does not expose feature_names_in_."
        )

    features = list(
        model_template.feature_names_in_
    )

    print()
    print(
        "Model features:"
    )

    for feature in features:

        print(
            f"  - {feature}"
        )

    # ========================================================
    # VALIDATE DATA
    # ========================================================

    required_columns = (
        features
        + [
            "result",
            "match_date",
        ]
    )

    missing = [
        column
        for column
        in required_columns
        if column not in df.columns
    ]

    if missing:

        raise ValueError(
            "Missing columns: "
            + ", ".join(missing)
        )

    # ========================================================
    # CLEAN
    # ========================================================

    df[
        "match_date"
    ] = pd.to_datetime(
        df[
            "match_date"
        ],
        errors="coerce",
    )

    df[
        "result"
    ] = df[
        "result"
    ].apply(
        normalize_result
    )

    df = df.dropna(
        subset=required_columns
    ).copy()

    df = df[
        df[
            "result"
        ].isin(
            [
                "HOME",
                "DRAW",
                "AWAY",
            ]
        )
    ].copy()

    df = df.sort_values(
        "match_date"
    ).reset_index(
        drop=True
    )

    print(
        f"Usable rows: {len(df)}"
    )

    # ========================================================
    # STRICT TIME SPLIT 80 / 20
    # ========================================================

    split_index = int(
        len(df)
        * 0.80
    )

    development = df.iloc[
        :split_index
    ].copy()

    holdout = df.iloc[
        split_index:
    ].copy()

    print()
    print(
        f"Development: {len(development)}"
    )

    print(
        f"Holdout: {len(holdout)}"
    )

    print(
        "Development dates:"
        f" {development['match_date'].min()}"
        f" -> {development['match_date'].max()}"
    )

    print(
        "Holdout dates:"
        f" {holdout['match_date'].min()}"
        f" -> {holdout['match_date'].max()}"
    )

    # ========================================================
    # IMPORTANT:
    #
    # Clone the production architecture and refit ONLY on
    # development data. This prevents holdout leakage.
    # ========================================================

    model = clone(
        model_template
    )

    model.fit(
        development[
            features
        ],
        development[
            "result"
        ],
    )

    # ========================================================
    # PREDICT HOLDOUT
    # ========================================================

    probabilities = (
        model.predict_proba(
            holdout[
                features
            ]
        )
    )

    classes = [
        str(value).upper()
        for value
        in model.classes_
    ]

    y_true = (
        holdout[
            "result"
        ]
        .tolist()
    )

    predicted_indexes = np.argmax(
        probabilities,
        axis=1,
    )

    predictions = [
        classes[index]
        for index
        in predicted_indexes
    ]

    confidence = np.max(
        probabilities,
        axis=1,
    )

    correct = np.array(
        [
            predicted == actual
            for predicted, actual
            in zip(
                predictions,
                y_true,
            )
        ],
        dtype=bool,
    )

    # ========================================================
    # METRICS
    # ========================================================

    accuracy = float(
        correct.mean()
    )

    loss = log_loss(
        y_true,
        probabilities,
        labels=classes,
    )

    brier = (
        multiclass_brier_score(
            y_true,
            probabilities,
            classes,
        )
    )

    print()
    print("=" * 80)
    print(
        "STRICT HOLDOUT METRICS"
    )
    print("=" * 80)

    print(
        f"Accuracy: "
        f"{accuracy * 100:.1f}%"
    )

    print(
        f"Log loss: "
        f"{loss:.4f}"
    )

    print(
        f"Multiclass Brier: "
        f"{brier:.4f}"
    )

    # ========================================================
    # OUTPUT
    # ========================================================

    output_columns = [
        column
        for column
        in [
            "match_id",
            "match_date",
            "league",
            "home_team",
            "away_team",
            "result",
        ]
        if column in holdout.columns
    ]

    output = holdout[
        output_columns
    ].copy()

    output[
        "prediction"
    ] = predictions

    output[
        "confidence"
    ] = (
        confidence
        * 100
    )

    output[
        "correct"
    ] = correct

    class_index = {
        name: index
        for index, name
        in enumerate(classes)
    }

    output[
        "home_probability"
    ] = (
        probabilities[
            :,
            class_index["HOME"]
        ]
        * 100
    )

    output[
        "draw_probability"
    ] = (
        probabilities[
            :,
            class_index["DRAW"]
        ]
        * 100
    )

    output[
        "away_probability"
    ] = (
        probabilities[
            :,
            class_index["AWAY"]
        ]
        * 100
    )

    # ========================================================
    # CONFIDENCE BUCKETS
    # ========================================================

    bins = [
        0,
        35,
        40,
        45,
        50,
        55,
        60,
        70,
        80,
        90,
        101,
    ]

    labels = [
        "<35",
        "35-39.9",
        "40-44.9",
        "45-49.9",
        "50-54.9",
        "55-59.9",
        "60-69.9",
        "70-79.9",
        "80-89.9",
        "90+",
    ]

    output[
        "confidence_bucket"
    ] = pd.cut(
        output[
            "confidence"
        ],
        bins=bins,
        labels=labels,
        right=False,
    )

    print()
    print("=" * 80)
    print(
        "CONFIDENCE CALIBRATION"
    )
    print("=" * 80)

    calibration_rows = []

    grouped = output.groupby(
        "confidence_bucket",
        observed=True,
    )

    for bucket, group in grouped:

        avg_confidence = float(
            group[
                "confidence"
            ].mean()
        )

        observed_accuracy = float(
            group[
                "correct"
            ].mean()
            * 100
        )

        gap = (
            avg_confidence
            - observed_accuracy
        )

        calibration_rows.append(
            {
                "bucket":
                    str(bucket),

                "matches":
                    len(group),

                "average_confidence":
                    avg_confidence,

                "observed_accuracy":
                    observed_accuracy,

                "calibration_gap":
                    gap,
            }
        )

        print(
            f"{str(bucket):>10}"
            f" | n={len(group):>4}"
            f" | predicted={avg_confidence:>5.1f}%"
            f" | actual={observed_accuracy:>5.1f}%"
            f" | gap={gap:>+6.1f}%"
        )

    # ========================================================
    # ECE
    # ========================================================

    ece = 0.0

    total = len(output)

    for row in calibration_rows:

        weight = (
            row[
                "matches"
            ]
            / total
        )

        ece += (
            weight
            * abs(
                row[
                    "calibration_gap"
                ]
            )
        )

    print()
    print(
        f"Expected Calibration Error: "
        f"{ece:.2f}%"
    )

    # ========================================================
    # SAVE
    # ========================================================

    REPORT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output.to_csv(
        REPORT_DIR
        / "probability_calibration.csv",
        index=False,
    )

    pd.DataFrame(
        calibration_rows
    ).to_csv(
        REPORT_DIR
        / "probability_calibration_buckets.csv",
        index=False,
    )

    print()
    print(
        "Saved:"
    )

    print(
        REPORT_DIR
        / "probability_calibration.csv"
    )

    print(
        REPORT_DIR
        / "probability_calibration_buckets.csv"
    )

    print("=" * 80)


if __name__ == "__main__":
    run()