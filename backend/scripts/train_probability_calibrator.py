from pathlib import Path
import json

import joblib
import numpy as np
import pandas as pd

from sklearn.base import clone
from sklearn.calibration import (
    CalibratedClassifierCV,
)
from sklearn.metrics import (
    log_loss,
)


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

OUTPUT_DIR = (
    BASE_DIR
    / "models"
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


def create_calibrator(
    estimator,
    method,
):

    try:

        return CalibratedClassifierCV(
            estimator=estimator,
            method=method,
            cv="prefit",
        )

    except TypeError:

        return CalibratedClassifierCV(
            base_estimator=estimator,
            method=method,
            cv="prefit",
        )


def accuracy_from_probabilities(
    probabilities,
    classes,
    y_true,
):

    indexes = np.argmax(
        probabilities,
        axis=1,
    )

    predictions = [
        classes[index]
        for index
        in indexes
    ]

    correct = [
        predicted == actual
        for predicted, actual
        in zip(
            predictions,
            y_true,
        )
    ]

    return (
        sum(correct)
        / len(correct)
    )


# ============================================================
# MAIN
# ============================================================

def run():

    print()
    print("=" * 80)
    print(
        "ANALITIKO PROBABILITY CALIBRATOR"
    )
    print("=" * 80)

    df = pd.read_csv(
        DATA_PATH
    )

    template = joblib.load(
        MODEL_PATH
    )

    features = list(
        template.feature_names_in_
    )

    required = (
        features
        + [
            "result",
            "match_date",
        ]
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
        subset=required
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

    n = len(df)

    base_end = int(
        n * 0.60
    )

    calibration_end = int(
        n * 0.80
    )

    base_df = df.iloc[
        :base_end
    ].copy()

    calibration_df = df.iloc[
        base_end:
        calibration_end
    ].copy()

    test_df = df.iloc[
        calibration_end:
    ].copy()

    print(
        f"Total: {n}"
    )

    print(
        f"Base train: {len(base_df)}"
    )

    print(
        f"Calibration: {len(calibration_df)}"
    )

    print(
        f"Untouched test: {len(test_df)}"
    )

    print()
    print(
        "Test dates:"
        f" {test_df['match_date'].min()}"
        f" -> {test_df['match_date'].max()}"
    )

    # ========================================================
    # TRAIN BASE MODEL
    # ========================================================

    base_model = clone(
        template
    )

    base_model.fit(
        base_df[
            features
        ],
        base_df[
            "result"
        ],
    )

    X_calibration = (
        calibration_df[
            features
        ]
    )

    y_calibration = (
        calibration_df[
            "result"
        ]
    )

    X_test = (
        test_df[
            features
        ]
    )

    y_test = (
        test_df[
            "result"
        ]
        .tolist()
    )

    classes = [
        str(value).upper()
        for value
        in base_model.classes_
    ]

    # ========================================================
    # RAW
    # ========================================================

    raw_probabilities = (
        base_model.predict_proba(
            X_test
        )
    )

    raw_loss = log_loss(
        y_test,
        raw_probabilities,
        labels=classes,
    )

    raw_accuracy = (
        accuracy_from_probabilities(
            raw_probabilities,
            classes,
            y_test,
        )
    )

    # ========================================================
    # SIGMOID
    # ========================================================

    sigmoid = create_calibrator(
        base_model,
        "sigmoid",
    )

    sigmoid.fit(
        X_calibration,
        y_calibration,
    )

    sigmoid_classes = [
        str(value).upper()
        for value
        in sigmoid.classes_
    ]

    sigmoid_probabilities = (
        sigmoid.predict_proba(
            X_test
        )
    )

    sigmoid_loss = log_loss(
        y_test,
        sigmoid_probabilities,
        labels=sigmoid_classes,
    )

    sigmoid_accuracy = (
        accuracy_from_probabilities(
            sigmoid_probabilities,
            sigmoid_classes,
            y_test,
        )
    )

    # ========================================================
    # ISOTONIC
    # ========================================================

    isotonic = create_calibrator(
        base_model,
        "isotonic",
    )

    isotonic.fit(
        X_calibration,
        y_calibration,
    )

    isotonic_classes = [
        str(value).upper()
        for value
        in isotonic.classes_
    ]

    isotonic_probabilities = (
        isotonic.predict_proba(
            X_test
        )
    )

    isotonic_loss = log_loss(
        y_test,
        isotonic_probabilities,
        labels=isotonic_classes,
    )

    isotonic_accuracy = (
        accuracy_from_probabilities(
            isotonic_probabilities,
            isotonic_classes,
            y_test,
        )
    )

    # ========================================================
    # RESULTS
    # ========================================================

    print()
    print("=" * 80)
    print(
        "CALIBRATION COMPARISON"
    )
    print("=" * 80)

    print(
        f"RAW      "
        f"| logloss={raw_loss:.5f}"
        f" | accuracy={raw_accuracy * 100:.1f}%"
    )

    print(
        f"SIGMOID  "
        f"| logloss={sigmoid_loss:.5f}"
        f" | accuracy={sigmoid_accuracy * 100:.1f}%"
    )

    print(
        f"ISOTONIC "
        f"| logloss={isotonic_loss:.5f}"
        f" | accuracy={isotonic_accuracy * 100:.1f}%"
    )

    candidates = {
        "raw": {
            "log_loss":
                raw_loss,

            "accuracy":
                raw_accuracy,

            "model":
                base_model,
        },

        "sigmoid": {
            "log_loss":
                sigmoid_loss,

            "accuracy":
                sigmoid_accuracy,

            "model":
                sigmoid,
        },

        "isotonic": {
            "log_loss":
                isotonic_loss,

            "accuracy":
                isotonic_accuracy,

            "model":
                isotonic,
        },
    }

    best_name = min(
        candidates,
        key=lambda name:
            candidates[
                name
            ][
                "log_loss"
            ],
    )

    best = candidates[
        best_name
    ]

    print()
    print(
        f"BEST: {best_name.upper()}"
    )

    print(
        f"Log loss: "
        f"{best['log_loss']:.5f}"
    )

    print(
        f"Accuracy: "
        f"{best['accuracy'] * 100:.1f}%"
    )

    # ========================================================
    # SAVE CANDIDATE
    # ========================================================

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    candidate_path = (
        OUTPUT_DIR
        / "probability_calibrator_candidate.joblib"
    )

    metadata_path = (
        OUTPUT_DIR
        / "probability_calibrator_metadata.json"
    )

    joblib.dump(
        best[
            "model"
        ],
        candidate_path,
    )

    metadata = {
        "status":
            "research_candidate",

        "production_model_unchanged":
            True,

        "method":
            best_name,

        "total_rows":
            n,

        "base_train_rows":
            len(base_df),

        "calibration_rows":
            len(calibration_df),

        "test_rows":
            len(test_df),

        "raw_log_loss":
            float(raw_loss),

        "sigmoid_log_loss":
            float(sigmoid_loss),

        "isotonic_log_loss":
            float(isotonic_loss),

        "raw_accuracy":
            float(
                raw_accuracy
                * 100
            ),

        "sigmoid_accuracy":
            float(
                sigmoid_accuracy
                * 100
            ),

        "isotonic_accuracy":
            float(
                isotonic_accuracy
                * 100
            ),
    }

    with open(
        metadata_path,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            metadata,
            file,
            indent=2,
        )

    print()
    print(
        f"Saved candidate: "
        f"{candidate_path}"
    )

    print(
        f"Saved metadata: "
        f"{metadata_path}"
    )

    print()
    print(
        "IMPORTANT: result_model.joblib "
        "was NOT modified."
    )

    print("=" * 80)


if __name__ == "__main__":
    run()