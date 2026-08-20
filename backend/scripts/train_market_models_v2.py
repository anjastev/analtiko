from pathlib import Path

import joblib
import pandas as pd

from sklearn.compose import (
    ColumnTransformer,
)
from sklearn.linear_model import (
    LogisticRegression,
)
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


NUMERIC_FEATURES_V2 = [
    "home_form",
    "away_form",

    "home_goals_avg",
    "away_goals_avg",

    "home_goals_against_avg",
    "away_goals_against_avg",

    "home_form_3",
    "away_form_3",
    "recent_form_diff_3",

    "home_home_ppg",
    "away_away_ppg",

    "home_home_goals_avg",
    "away_away_goals_avg",

    "home_home_conceded_avg",
    "away_away_conceded_avg",

    "home_home_goal_diff_avg",
    "away_away_goal_diff_avg",

    "home_home_clean_sheet_rate",
    "away_away_clean_sheet_rate",

    "home_home_failed_score_rate",
    "away_away_failed_score_rate",

    "home_home_win_rate",
    "away_away_win_rate",

    "home_away_context_diff",

    "home_xg",
    "away_xg",

    "h2h_home_score",
    "h2h_away_score",
    "h2h_matches",
]


CATEGORICAL_FEATURES = [
    "league",
]


FEATURES_V2 = (
    NUMERIC_FEATURES_V2
    + CATEGORICAL_FEATURES
)


TARGETS = {
    "over_25": (
        MODELS_DIR
        / "over25_model_v2_candidate.joblib"
    ),

    "btts": (
        MODELS_DIR
        / "btts_model_v2_candidate.joblib"
    ),
}


def build_pipeline():

    preprocessor = (
        ColumnTransformer(
            transformers=[
                (
                    "numeric",
                    StandardScaler(),
                    NUMERIC_FEATURES_V2,
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

    return Pipeline(
        steps=[
            (
                "preprocessor",
                preprocessor,
            ),
            (
                "model",
                LogisticRegression(
                    C=0.1,
                    max_iter=3000,
                ),
            ),
        ]
    )


def run():

    df = pd.read_csv(
        DATASET_FILE
    )

    MODELS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print()
    print("=" * 80)
    print(
        "ANALITIKO MARKET MODEL V2 TRAINING"
    )
    print("=" * 80)

    print(
        f"Dataset rows: "
        f"{len(df)}"
    )

    for target, output_file in (
        TARGETS.items()
    ):

        required = (
            FEATURES_V2
            + [target]
        )

        missing_columns = [
            column
            for column in required
            if column
            not in df.columns
        ]

        if missing_columns:

            raise RuntimeError(
                f"Missing columns: "
                f"{missing_columns}"
            )

        model_df = (
            df[
                required
            ]
            .dropna()
            .copy()
        )

        X = (
            model_df[
                FEATURES_V2
            ]
        )

        y = (
            model_df[
                target
            ]
            .astype(int)
        )

        model = (
            build_pipeline()
        )

        model.fit(
            X,
            y,
        )

        joblib.dump(
            model,
            output_file,
        )

        print()
        print(
            f"{target}"
        )

        print(
            f"Rows: "
            f"{len(model_df)}"
        )

        print(
            f"Saved: "
            f"{output_file}"
        )

    print()
    print(
        "STATUS: OK"
    )

    print("=" * 80)


if __name__ == "__main__":
    run()