from pathlib import Path

import joblib
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


DATA_FILE = Path(
    "data/analitiko_dataset.csv"
)

MODEL_DIR = Path(
    "models"
)

MODEL_FILE = (
    MODEL_DIR
    / "result_model.joblib"
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


def run():
    if not DATA_FILE.exists():
        print(
            f"Dataset not found: "
            f"{DATA_FILE.resolve()}"
        )
        return

    data = pd.read_csv(
        DATA_FILE
    )

    print()
    print("=" * 70)
    print("ANALITIKO ML TRAINING")
    print("=" * 70)

    print(
        f"Dataset rows: "
        f"{len(data)}"
    )

    if len(data) < 3:
        print(
            "Not enough data to train."
        )
        return

    print()
    print("Target distribution:")

    print(
        data[TARGET]
        .value_counts()
        .to_string()
    )

    unique_classes = (
        data[TARGET]
        .nunique()
    )

    if unique_classes < 2:
        print()
        print(
            "Cannot train classifier: "
            "dataset contains only one result class."
        )
        return

    X = data[
        NUMERIC_FEATURES
        + CATEGORICAL_FEATURES
    ]

    y = data[TARGET]

    numeric_transformer = (
        StandardScaler()
    )

    categorical_transformer = (
        OneHotEncoder(
            handle_unknown="ignore",
        )
    )

    preprocessor = (
        ColumnTransformer(
            transformers=[
                (
                    "numeric",
                    numeric_transformer,
                    NUMERIC_FEATURES,
                ),

                (
                    "categorical",
                    categorical_transformer,
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

    pipeline = (
        Pipeline(
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
    )

    pipeline.fit(
        X,
        y,
    )

    MODEL_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    joblib.dump(
        pipeline,
        MODEL_FILE,
    )

    print()
    print(
        "Model trained successfully."
    )

    print(
        f"Classes: "
        f"{list(pipeline.named_steps['model'].classes_)}"
    )

    print(
        f"Saved to: "
        f"{MODEL_FILE.resolve()}"
    )

    print()
    print(
        "NOTE: Dataset is currently too small "
        "for meaningful accuracy evaluation."
    )


if __name__ == "__main__":
    run()