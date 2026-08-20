from pathlib import Path

import joblib
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import (
    OneHotEncoder,
    StandardScaler,
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


FEATURES = (
    NUMERIC_FEATURES
    + CATEGORICAL_FEATURES
)


TARGETS = {
    "over_25": (
        MODELS_DIR
        / "over25_model.joblib"
    ),
    "btts": (
        MODELS_DIR
        / "btts_model.joblib"
    ),
}


def build_pipeline():

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

    if not DATASET_FILE.exists():
        raise FileNotFoundError(
            f"Dataset not found: "
            f"{DATASET_FILE}"
        )

    MODELS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    df = pd.read_csv(
        DATASET_FILE
    )

    print()
    print("=" * 80)
    print(
        "ANALITIKO FOOTBALL MARKET MODEL TRAINING"
    )
    print("=" * 80)

    print(
        f"Dataset rows: "
        f"{len(df)}"
    )

    for target, output_file in (
        TARGETS.items()
    ):

        print()
        print("-" * 80)

        print(
            f"Target: "
            f"{target}"
        )

        required_columns = (
            FEATURES
            + [target]
        )

        missing = [
            column
            for column in required_columns
            if column not in df.columns
        ]

        if missing:
            raise RuntimeError(
                f"Missing columns for {target}: "
                f"{missing}"
            )

        model_df = (
            df[
                required_columns
            ]
            .dropna()
            .copy()
        )

        X = model_df[
            FEATURES
        ]

        y = model_df[
            target
        ]

        print(
            f"Training rows: "
            f"{len(model_df)}"
        )

        print(
            f"Classes: "
            f"{sorted(y.unique().tolist())}"
        )

        pipeline = (
            build_pipeline()
        )

        pipeline.fit(
            X,
            y,
        )

        joblib.dump(
            pipeline,
            output_file,
        )

        print(
            f"Saved: "
            f"{output_file}"
        )

    print()
    print("=" * 80)
    print(
        "STATUS: OK"
    )
    print("=" * 80)


if __name__ == "__main__":
    run()