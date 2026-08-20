from pathlib import Path

import joblib
import pandas as pd


LEAGUE_THRESHOLDS = {
    "Bundesliga": 48.0,
    "La Liga": 50.0,
    "Premier League": 48.0,
    "Serie A": 48.0,
}


DEFAULT_THRESHOLD = 50.0


MODEL_FILE = (
    Path(__file__)
    .resolve()
    .parents[2]
    / "models"
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


_model = None


def get_model():

    global _model

    if _model is None:

        if not MODEL_FILE.exists():

            raise FileNotFoundError(
                f"ML model not found: "
                f"{MODEL_FILE}"
            )

        _model = joblib.load(
            MODEL_FILE
        )

    return _model


def predict_result(
    *,
    league: str,

    home_form: float,
    away_form: float,

    home_goals_avg: float,
    away_goals_avg: float,

    home_goals_against_avg: float,
    away_goals_against_avg: float,

    home_xg: float,
    away_xg: float,

    h2h_home_score: float,
    h2h_away_score: float,
    h2h_matches: int,
) -> dict:

    model = get_model()


    # ========================================================
    # INPUT ROW
    # ========================================================

    row = {
        "home_form":
            home_form,

        "away_form":
            away_form,

        "home_goals_avg":
            home_goals_avg,

        "away_goals_avg":
            away_goals_avg,

        "home_goals_against_avg":
            home_goals_against_avg,

        "away_goals_against_avg":
            away_goals_against_avg,

        "home_xg":
            home_xg,

        "away_xg":
            away_xg,

        "h2h_home_score":
            h2h_home_score,

        "h2h_away_score":
            h2h_away_score,

        "h2h_matches":
            h2h_matches,

        "league":
            league,
    }


    data = pd.DataFrame(
        [row]
    )


    # ========================================================
    # PREDICTION
    # ========================================================

    prediction = (
        model.predict(
            data
        )[0]
    )


    probabilities = (
        model.predict_proba(
            data
        )[0]
    )


    classes = (
        model
        .named_steps["model"]
        .classes_
    )


    # ========================================================
    # PROBABILITY MAP
    # ========================================================

    probability_map = {

        str(class_name):
            round(
                float(probability)
                * 100,
                1,
            )

        for (
            class_name,
            probability,
        ) in zip(
            classes,
            probabilities,
        )
    }


    home_probability = (
        probability_map.get(
            "HOME",
            0.0,
        )
    )


    draw_probability = (
        probability_map.get(
            "DRAW",
            0.0,
        )
    )


    away_probability = (
        probability_map.get(
            "AWAY",
            0.0,
        )
    )


    # ========================================================
    # CONFIDENCE + MARGIN
    # ========================================================

    sorted_probabilities = sorted(
        [
            home_probability,
            draw_probability,
            away_probability,
        ],
        reverse=True,
    )


    top_probability = (
        sorted_probabilities[0]
    )


    second_probability = (
        sorted_probabilities[1]
    )


    margin = (
        top_probability
        - second_probability
    )


    # ========================================================
    # ANALITIKO SCORE
    #
    # 70% top prediction probability
    # 30% distance from second-best prediction
    # ========================================================

    analitiko_score = (
        top_probability * 0.70
        +
        margin * 0.30
    )


    # ========================================================
    # LEAGUE-SPECIFIC STRONG PICK THRESHOLD
    # ========================================================

    league_threshold = (
        LEAGUE_THRESHOLDS.get(
            league,
            DEFAULT_THRESHOLD,
        )
    )


    is_strong_pick = (
        analitiko_score
        >= league_threshold
    )

    ELITE_THRESHOLD = 50.0

    is_elite_pick = (
            analitiko_score
            >= ELITE_THRESHOLD
    )


    # ========================================================
    # DISPLAY CONFIDENCE LEVEL
    #
    # Important:
    # STRONG is based on league-specific validated threshold.
    # ========================================================

    if is_elite_pick:
        confidence_level = "ELITE"

    elif is_strong_pick:
        confidence_level = "STRONG"

    elif analitiko_score >= 40:
        confidence_level = "MEDIUM"

    else:
        confidence_level = "LOW"




    # ========================================================
    # RETURN
    # ========================================================

    return {
        "pick":
            str(prediction),

        "probabilities": {
            "HOME":
                home_probability,

            "DRAW":
                draw_probability,

            "AWAY":
                away_probability,
        },

        "confidence":
            round(
                top_probability,
                1,
            ),

        "margin":
            round(
                margin,
                1,
            ),

        "analitiko_score":
            round(
                analitiko_score,
                1,
            ),

        "league_threshold":
            round(
                league_threshold,
                1,
            ),

        "is_strong_pick":
            is_strong_pick,

        "confidence_level":
            confidence_level,

        "trained_classes": [
            str(item)
            for item in classes
        ],

        "experimental":
            True,

        "elite_threshold":
            ELITE_THRESHOLD,

        "is_elite_pick":
            is_elite_pick,
    }