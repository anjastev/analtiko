from pathlib import Path

import joblib
import numpy as np
import pandas as pd


# ============================================================
# CONFIG
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]

DATA_PATH = (
    BASE_DIR
    / "data"
    / "analitiko_dataset.csv"
)

CALIBRATOR_PATH = (
    BASE_DIR
    / "models"
    / "probability_calibrator_candidate.joblib"
)

REPORT_PATH = (
    BASE_DIR
    / "data"
    / "reports"
    / "value_edges.csv"
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


def implied_probability(odds):

    if (
        pd.isna(odds)
        or float(odds) <= 1.0
    ):

        return None

    return (
        1.0
        / float(odds)
    )


def remove_margin(
    home,
    draw,
    away,
):

    total = (
        home
        + draw
        + away
    )

    return {
        "HOME":
            home / total,

        "DRAW":
            draw / total,

        "AWAY":
            away / total,
    }


# ============================================================
# MAIN
# ============================================================

def run():

    print()
    print("=" * 90)
    print(
        "ANALITIKO HISTORICAL VALUE EDGE RESEARCH"
    )
    print("=" * 90)

    if not CALIBRATOR_PATH.exists():

        raise FileNotFoundError(
            "Calibration candidate does not exist.\n"
            "Run first:\n"
            "python -X utf8 -m "
            "scripts.train_probability_calibrator"
        )

    df = pd.read_csv(
        DATA_PATH
    )

    model = joblib.load(
        CALIBRATOR_PATH
    )

    features = list(
        model.feature_names_in_
    )

    required = (
        features
        + [
            "home_odds",
            "draw_odds",
            "away_odds",
        ]
    )

    missing = [
        column
        for column
        in required
        if column not in df.columns
    ]

    if missing:

        raise ValueError(
            "Missing columns: "
            + ", ".join(missing)
        )

    # ========================================================
    # ODDS FILTER
    # ========================================================

    odds_df = df.dropna(
        subset=[
            "home_odds",
            "draw_odds",
            "away_odds",
        ]
    ).copy()

    odds_df = odds_df[
        (
            odds_df[
                "home_odds"
            ] > 1
        )
        &
        (
            odds_df[
                "draw_odds"
            ] > 1
        )
        &
        (
            odds_df[
                "away_odds"
            ] > 1
        )
    ].copy()

    print(
        f"Dataset rows: {len(df)}"
    )

    print(
        f"Rows with usable odds: "
        f"{len(odds_df)}"
    )

    if len(odds_df) == 0:

        print()
        print(
            "No historical odds available."
        )

        return

    if len(odds_df) < 30:

        print()
        print(
            "WARNING:"
        )

        print(
            "Historical odds sample is too small "
            "for reliable betting conclusions."
        )

        print(
            "Edges below are exploratory only."
        )

    # ========================================================
    # MODEL PROBABILITIES
    # ========================================================

    probabilities = (
        model.predict_proba(
            odds_df[
                features
            ]
        )
    )

    classes = [
        str(value).upper()
        for value
        in model.classes_
    ]

    class_index = {
        name: index
        for index, name
        in enumerate(classes)
    }

    rows = []

    # ========================================================
    # EDGE CALCULATION
    # ========================================================

    for position, (
        _,
        row,
    ) in enumerate(
        odds_df.iterrows()
    ):

        model_probabilities = {
            "HOME":
                float(
                    probabilities[
                        position,
                        class_index[
                            "HOME"
                        ]
                    ]
                ),

            "DRAW":
                float(
                    probabilities[
                        position,
                        class_index[
                            "DRAW"
                        ]
                    ]
                ),

            "AWAY":
                float(
                    probabilities[
                        position,
                        class_index[
                            "AWAY"
                        ]
                    ]
                ),
        }

        raw_home = (
            implied_probability(
                row[
                    "home_odds"
                ]
            )
        )

        raw_draw = (
            implied_probability(
                row[
                    "draw_odds"
                ]
            )
        )

        raw_away = (
            implied_probability(
                row[
                    "away_odds"
                ]
            )
        )

        market = remove_margin(
            raw_home,
            raw_draw,
            raw_away,
        )

        odds_map = {
            "HOME":
                float(
                    row[
                        "home_odds"
                    ]
                ),

            "DRAW":
                float(
                    row[
                        "draw_odds"
                    ]
                ),

            "AWAY":
                float(
                    row[
                        "away_odds"
                    ]
                ),
        }

        edges = {
            pick:
                (
                    model_probabilities[pick]
                    -
                    market[pick]
                )
            for pick
            in [
                "HOME",
                "DRAW",
                "AWAY",
            ]
        }

        expected_values = {
            pick:
                (
                    model_probabilities[
                        pick
                    ]
                    * odds_map[
                        pick
                    ]
                    - 1.0
                )
            for pick
            in [
                "HOME",
                "DRAW",
                "AWAY",
            ]
        }

        best_pick = max(
            edges,
            key=edges.get,
        )

        best_probability = (
            model_probabilities[
                best_pick
            ]
        )

        fair_odds = (
            1.0
            / best_probability
            if best_probability > 0
            else None
        )

        actual = normalize_result(
            row.get(
                "result",
                "",
            )
        )

        rows.append(
            {
                "match_id":
                    row.get(
                        "match_id"
                    ),

                "match_date":
                    row.get(
                        "match_date"
                    ),

                "league":
                    row.get(
                        "league"
                    ),

                "home_team":
                    row.get(
                        "home_team"
                    ),

                "away_team":
                    row.get(
                        "away_team"
                    ),

                "actual_result":
                    actual,

                "best_value_pick":
                    best_pick,

                "model_probability":
                    best_probability
                    * 100,

                "market_probability":
                    market[
                        best_pick
                    ]
                    * 100,

                "edge":
                    edges[
                        best_pick
                    ]
                    * 100,

                "market_odds":
                    odds_map[
                        best_pick
                    ],

                "fair_odds":
                    fair_odds,

                "expected_value":
                    expected_values[
                        best_pick
                    ]
                    * 100,

                "correct":
                    (
                        actual
                        == best_pick
                    ),

                "home_edge":
                    edges[
                        "HOME"
                    ]
                    * 100,

                "draw_edge":
                    edges[
                        "DRAW"
                    ]
                    * 100,

                "away_edge":
                    edges[
                        "AWAY"
                    ]
                    * 100,
            }
        )

    result = pd.DataFrame(
        rows
    )

    result = result.sort_values(
        [
            "edge",
            "expected_value",
        ],
        ascending=False,
    )

    # ========================================================
    # DISPLAY
    # ========================================================

    print()
    print("=" * 90)
    print(
        "TOP VALUE EDGES"
    )
    print("=" * 90)

    columns = [
        "home_team",
        "away_team",
        "best_value_pick",
        "model_probability",
        "market_probability",
        "edge",
        "market_odds",
        "fair_odds",
        "expected_value",
    ]

    print(
        result[
            columns
        ]
        .head(
            20
        )
        .to_string(
            index=False
        )
    )

    # ========================================================
    # SAVE
    # ========================================================

    REPORT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    result.to_csv(
        REPORT_PATH,
        index=False,
    )

    print()
    print(
        f"Saved: {REPORT_PATH}"
    )

    print("=" * 90)


if __name__ == "__main__":
    run()