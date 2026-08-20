from pathlib import Path

import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import (
    RandomForestClassifier,
    HistGradientBoostingClassifier,
)
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
]


CATEGORICAL_FEATURES = [
    "league",
]


TARGET = "result"

TEST_RATIO = 0.20


def run():
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


    split_index = int(
        len(data)
        * (1 - TEST_RATIO)
    )


    train_data = (
        data.iloc[
            :split_index
        ]
    )

    test_data = (
        data.iloc[
            split_index:
        ]
    )


    features = (
        NUMERIC_FEATURES
        + CATEGORICAL_FEATURES
    )


    X_train = (
        train_data[
            features
        ]
    )

    y_train = (
        train_data[
            TARGET
        ]
    )


    X_test = (
        test_data[
            features
        ]
    )

    y_test = (
        test_data[
            TARGET
        ]
    )


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
                        handle_unknown="ignore",
                        sparse_output=False,
                    ),
                    CATEGORICAL_FEATURES,
                ),
            ],
            sparse_threshold=0,
        )
    )


    models = {
        "Logistic Regression":
            LogisticRegression(
                C=0.1,
                max_iter=3000,
                class_weight=None,
            ),

        "Random Forest":
            RandomForestClassifier(
                n_estimators=400,
                max_depth=8,
                min_samples_leaf=4,
                class_weight="balanced",
                random_state=42,
            ),

        "Gradient Boosting":
            HistGradientBoostingClassifier(
                max_iter=250,
                learning_rate=0.05,
                max_leaf_nodes=15,
                l2_regularization=1.0,
                random_state=42,
            ),
    }


    print()
    print("=" * 70)
    print("ANALITIKO MODEL COMPARISON")
    print("=" * 70)

    print(
        f"Training rows: "
        f"{len(train_data)}"
    )

    print(
        f"Testing rows: "
        f"{len(test_data)}"
    )


    results = []


    for name, classifier in (
        models.items()
    ):

        pipeline = (
            Pipeline(
                steps=[
                    (
                        "preprocessor",
                        preprocessor,
                    ),

                    (
                        "model",
                        classifier,
                    ),
                ]
            )
        )


        pipeline.fit(
            X_train,
            y_train,
        )


        predictions = (
            pipeline.predict(
                X_test
            )
        )


        accuracy = (
            accuracy_score(
                y_test,
                predictions,
            )
        )


        results.append(
            (
                name,
                accuracy,
            )
        )


        print()
        print(
            f"{name}: "
            f"{accuracy * 100:.1f}%"
        )


    results.sort(
        key=lambda item:
            item[1],
        reverse=True,
    )


    print()
    print("=" * 70)
    print("RANKING")
    print("=" * 70)


    for index, (
        name,
        accuracy,
    ) in enumerate(
        results,
        start=1,
    ):

        print(
            f"{index}. "
            f"{name}: "
            f"{accuracy * 100:.1f}%"
        )


if __name__ == "__main__":
    run()