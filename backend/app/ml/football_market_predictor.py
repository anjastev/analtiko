from pathlib import Path

import joblib
import pandas as pd


BASE_DIR = (
    Path(__file__)
    .resolve()
    .parents[2]
)


OVER25_MODEL_FILE = (
    BASE_DIR
    / "models"
    / "over25_model.joblib"
)


BTTS_MODEL_FILE = (
    BASE_DIR
    / "models"
    / "btts_model.joblib"
)


_models = {}


def get_model(
    model_name: str,
):

    if model_name in _models:
        return _models[
            model_name
        ]

    if model_name == "over25":
        file_path = (
            OVER25_MODEL_FILE
        )

    elif model_name == "btts":
        file_path = (
            BTTS_MODEL_FILE
        )

    else:
        raise ValueError(
            f"Unknown model: "
            f"{model_name}"
        )

    if not file_path.exists():

        raise FileNotFoundError(
            f"Model not found: "
            f"{file_path}"
        )

    model = joblib.load(
        file_path
    )

    _models[
        model_name
    ] = model

    return model


def build_input_row(
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
):

    return {
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


def predict_binary_market(
    model_name: str,
    positive_label,
    negative_selection: str,
    positive_selection: str,
    **features,
):

    model = get_model(
        model_name
    )

    row = build_input_row(
        **features
    )

    data = pd.DataFrame(
        [row]
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

    probability_map = {
        class_name:
            float(probability)
        for (
            class_name,
            probability,
        )
        in zip(
            classes,
            probabilities,
        )
    }

    positive_probability = (
        probability_map.get(
            positive_label,
            0.0,
        )
        * 100.0
    )

    negative_probability = (
        100.0
        - positive_probability
    )

    if (
        positive_probability
        >= negative_probability
    ):

        pick = (
            positive_selection
        )

        confidence = (
            positive_probability
        )

    else:

        pick = (
            negative_selection
        )

        confidence = (
            negative_probability
        )

    return {
        "pick":
            pick,

        "probabilities": {
            positive_selection:
                round(
                    positive_probability,
                    1,
                ),

            negative_selection:
                round(
                    negative_probability,
                    1,
                ),
        },

        "confidence":
            round(
                confidence,
                1,
            ),
    }


def predict_over25(
    **features,
):

    return predict_binary_market(
        model_name="over25",
        positive_label=1,
        negative_selection="UNDER",
        positive_selection="OVER",
        **features,
    )


def predict_btts(
    **features,
):

    return predict_binary_market(
        model_name="btts",
        positive_label=1,
        negative_selection="NO",
        positive_selection="YES",
        **features,
    )