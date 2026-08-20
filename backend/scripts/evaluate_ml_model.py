from pathlib import Path

import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    classification_report,
    confusion_matrix,
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

    # ========================================================
    # CHECK DATASET
    # ========================================================

    if not DATA_FILE.exists():
        print()
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
    print("ANALITIKO ML BACKTEST")
    print("=" * 70)


    print()
    print(
        f"Dataset rows: "
        f"{len(data)}"
    )


    if len(data) < 20:
        print()
        print(
            "WARNING: Dataset is still very small."
        )

        print(
            "Backtest results will not be reliable yet."
        )


    # ========================================================
    # DATE SORTING
    # ========================================================

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


    # ========================================================
    # TRAIN / TEST SPLIT
    # ========================================================

    split_index = int(
        len(data)
        * (1 - TEST_RATIO)
    )


    split_index = max(
        1,
        min(
            split_index,
            len(data) - 1,
        ),
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


    print()
    print(
        f"Training rows: "
        f"{len(train_data)}"
    )

    print(
        f"Testing rows:  "
        f"{len(test_data)}"
    )


    print()
    print("Training period:")

    print(
        train_data[
            "match_date"
        ].min()
    )

    print("->")

    print(
        train_data[
            "match_date"
        ].max()
    )


    print()
    print("Testing period:")

    print(
        test_data[
            "match_date"
        ].min()
    )

    print("->")

    print(
        test_data[
            "match_date"
        ].max()
    )


    # ========================================================
    # FEATURES
    # ========================================================

    feature_columns = (
        NUMERIC_FEATURES
        + CATEGORICAL_FEATURES
    )


    missing_columns = [
        column
        for column in feature_columns
        if column not in data.columns
    ]


    if missing_columns:
        print()
        print(
            "Missing dataset columns:"
        )

        for column in missing_columns:
            print(
                f"- {column}"
            )

        print()
        print(
            "Run build_dataset again "
            "before evaluating."
        )

        return


    X_train = (
        train_data[
            feature_columns
        ]
    )


    y_train = (
        train_data[
            TARGET
        ]
    )


    X_test = (
        test_data[
            feature_columns
        ]
    )


    y_test = (
        test_data[
            TARGET
        ]
    )


    # ========================================================
    # CHECK CLASSES
    # ========================================================

    train_classes = (
        sorted(
            y_train.unique()
        )
    )


    print()
    print(
        "Training classes:"
    )

    print(
        train_classes
    )


    if len(train_classes) < 2:
        print()
        print(
            "Cannot train model: "
            "training data contains "
            "fewer than two classes."
        )

        return


    # ========================================================
    # PREPROCESSOR
    # ========================================================

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


    # ========================================================
    # MODEL
    # ========================================================

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


    # ========================================================
    # TRAIN
    # ========================================================

    pipeline.fit(
        X_train,
        y_train,
    )


    # ========================================================
    # PREDICT
    # ========================================================

    predictions = (
        pipeline.predict(
            X_test
        )
    )


    probabilities = (
        pipeline.predict_proba(
            X_test
        )
    )


    classes = (
        pipeline
        .named_steps["model"]
        .classes_
    )


    # ========================================================
    # CONFIDENCE SIGNALS
    # ========================================================

    confidence_scores = (
        probabilities.max(
            axis=1
        )
    )


    sorted_probabilities = (
        probabilities.copy()
    )


    sorted_probabilities.sort(
        axis=1
    )


    confidence_margins = (
        sorted_probabilities[:, -1]
        -
        sorted_probabilities[:, -2]
    )


    analitiko_confidence_scores = (
        confidence_scores * 0.70
        +
        confidence_margins * 0.30
    )


    # ========================================================
    # METRICS
    # ========================================================

    accuracy = (
        accuracy_score(
            y_test,
            predictions,
        )
    )


    balanced_accuracy = (
        balanced_accuracy_score(
            y_test,
            predictions,
        )
    )


    loss = (
        log_loss(
            y_test,
            probabilities,
            labels=classes,
        )
    )


    # ========================================================
    # RESULTS
    # ========================================================

    print()
    print("=" * 70)
    print("RESULTS")
    print("=" * 70)


    print()
    print(
        f"Accuracy: "
        f"{accuracy * 100:.1f}%"
    )

    print(
        f"Balanced accuracy: "
        f"{balanced_accuracy * 100:.1f}%"
    )

    print(
        f"Log loss: "
        f"{loss:.4f}"
    )


    # ========================================================
    # CLASSIFICATION REPORT
    # ========================================================

    print()
    print(
        "Classification report:"
    )


    print(
        classification_report(
            y_test,
            predictions,
            zero_division=0,
        )
    )


    # ========================================================
    # CONFUSION MATRIX
    # ========================================================

    labels = [
        "HOME",
        "DRAW",
        "AWAY",
    ]


    matrix = (
        confusion_matrix(
            y_test,
            predictions,
            labels=labels,
        )
    )


    print()
    print("Confusion Matrix")
    print("Rows = actual")
    print("Columns = predicted")
    print()

    print(
        "          HOME  DRAW  AWAY"
    )


    for label, row in zip(
        labels,
        matrix,
    ):

        print(
            f"{label:<8} "
            f"{row[0]:>5} "
            f"{row[1]:>5} "
            f"{row[2]:>5}"
        )


    # ========================================================
    # CONFIDENCE ANALYSIS
    # ========================================================

    print()
    print("=" * 70)
    print("CONFIDENCE ANALYSIS")
    print("=" * 70)


    thresholds = [
        0.35,
        0.40,
        0.45,
        0.50,
        0.55,
        0.60,
        0.65,
    ]


    y_test_array = (
        y_test.to_numpy()
    )


    for threshold in thresholds:

        mask = (
            confidence_scores
            >= threshold
        )

        selected_count = int(
            mask.sum()
        )


        if selected_count == 0:

            print(
                f"{threshold * 100:.0f}%+ "
                f"| Matches:   0 "
                f"| Coverage:   0.0% "
                f"| Accuracy:     -"
            )

            continue


        selected_accuracy = (
            accuracy_score(
                y_test_array[
                    mask
                ],
                predictions[
                    mask
                ],
            )
        )


        coverage = (
            selected_count
            / len(y_test_array)
            * 100
        )


        print(
            f"{threshold * 100:.0f}%+ "
            f"| Matches: "
            f"{selected_count:>3} "
            f"| Coverage: "
            f"{coverage:>5.1f}% "
            f"| Accuracy: "
            f"{selected_accuracy * 100:>5.1f}%"
        )


    # ========================================================
    # CONFIDENCE BANDS
    # ========================================================

    print()
    print("=" * 70)
    print("CONFIDENCE BANDS")
    print("=" * 70)


    bands = [
        (
            0.00,
            0.40,
            "<40%",
        ),

        (
            0.40,
            0.45,
            "40-45%",
        ),

        (
            0.45,
            0.50,
            "45-50%",
        ),

        (
            0.50,
            0.55,
            "50-55%",
        ),

        (
            0.55,
            0.60,
            "55-60%",
        ),

        (
            0.60,
            1.01,
            "60%+",
        ),
    ]


    for (
        minimum,
        maximum,
        label,
    ) in bands:

        mask = (
            (
                confidence_scores
                >= minimum
            )
            &
            (
                confidence_scores
                < maximum
            )
        )


        count = int(
            mask.sum()
        )


        if count == 0:

            print(
                f"{label:<10} "
                f"| Matches: 0"
            )

            continue


        band_accuracy = (
            accuracy_score(
                y_test_array[
                    mask
                ],
                predictions[
                    mask
                ],
            )
        )


        print(
            f"{label:<10} "
            f"| Matches: "
            f"{count:>3} "
            f"| Accuracy: "
            f"{band_accuracy * 100:>5.1f}%"
        )


    # ========================================================
    # ANALITIKO CONFIDENCE SCORE
    # ========================================================

    print()
    print("=" * 70)
    print("ANALITIKO CONFIDENCE SCORE")
    print("=" * 70)


    score_thresholds = [
        0.30,
        0.35,
        0.40,
        0.45,
        0.50,
        0.55,
    ]


    for threshold in score_thresholds:

        mask = (
            analitiko_confidence_scores
            >= threshold
        )


        count = int(
            mask.sum()
        )


        if count == 0:

            print(
                f"Score "
                f"{threshold * 100:.0f}+ "
                f"| Matches: 0"
            )

            continue


        selected_accuracy = (
            accuracy_score(
                y_test_array[
                    mask
                ],
                predictions[
                    mask
                ],
            )
        )


        coverage = (
            count
            / len(y_test_array)
            * 100
        )


        print(
            f"Score "
            f"{threshold * 100:.0f}+ "
            f"| Matches: "
            f"{count:>3} "
            f"| Coverage: "
            f"{coverage:>5.1f}% "
            f"| Accuracy: "
            f"{selected_accuracy * 100:>5.1f}%"
        )


    # ========================================================
    # PREDICTION MARGIN ANALYSIS
    # ========================================================

    print()
    print("=" * 70)
    print("PREDICTION MARGIN ANALYSIS")
    print("=" * 70)


    margin_thresholds = [
        0.02,
        0.05,
        0.10,
        0.15,
        0.20,
    ]


    for threshold in margin_thresholds:

        mask = (
            confidence_margins
            >= threshold
        )


        selected_count = int(
            mask.sum()
        )


        if selected_count == 0:

            print(
                f"Margin "
                f"{threshold * 100:.0f}%+ "
                f"| Matches: 0"
            )

            continue


        selected_accuracy = (
            accuracy_score(
                y_test_array[
                    mask
                ],
                predictions[
                    mask
                ],
            )
        )


        coverage = (
            selected_count
            / len(y_test_array)
            * 100
        )


        print(
            f"Margin "
            f"{threshold * 100:.0f}%+ "
            f"| Matches: "
            f"{selected_count:>3} "
            f"| Coverage: "
            f"{coverage:>5.1f}% "
            f"| Accuracy: "
            f"{selected_accuracy * 100:>5.1f}%"
        )


    # ========================================================
    # TEST MATCHES
    # ========================================================

    print()
    print("=" * 70)
    print("TEST MATCHES")
    print("=" * 70)


    for (
        test_index,
        (
            (_, row),
            predicted,
            probability_row,
        ),
    ) in enumerate(
        zip(
            test_data.iterrows(),
            predictions,
            probabilities,
        )
    ):

        probability_map = {
            class_name:
                probability * 100

            for (
                class_name,
                probability,
            ) in zip(
                classes,
                probability_row,
            )
        }


        actual = (
            row[
                TARGET
            ]
        )


        correct = (
            actual
            == predicted
        )


        predicted_probability = (
            probability_map.get(
                predicted,
                0,
            )
        )


        margin = (
            confidence_margins[
                test_index
            ]
            * 100
        )


        analitiko_score = (
            analitiko_confidence_scores[
                test_index
            ]
            * 100
        )


        print()

        print(
            f"{row['home_team']} "
            f"vs "
            f"{row['away_team']}"
        )


        print(
            f"Actual:    "
            f"{actual}"
        )


        print(
            f"Predicted: "
            f"{predicted}"
        )


        print(
            f"Probability: "
            f"{predicted_probability:.1f}%"
        )


        print(
            "Probabilities: "
            f"HOME "
            f"{probability_map.get('HOME', 0):.1f}% | "
            f"DRAW "
            f"{probability_map.get('DRAW', 0):.1f}% | "
            f"AWAY "
            f"{probability_map.get('AWAY', 0):.1f}%"
        )


        print(
            f"Margin: "
            f"{margin:.1f}%"
        )


        print(
            f"Analitiko score: "
            f"{analitiko_score:.1f}"
        )


        print(
            "Result: "
            f"{'CORRECT' if correct else 'WRONG'}"
        )


    # ========================================================
    # COMPLETE
    # ========================================================

    print()
    print("=" * 70)
    print("BACKTEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    run()