MARKET_MODEL_REGISTRY = {
    "1X2": {
        "production": (
            "result_model.joblib"
        ),
        "version": (
            "logistic_regression_v2"
        ),
        "status": (
            "ACTIVE"
        ),
    },

    "OU_25": {
        "production": (
            "over25_model.joblib"
        ),
        "candidate": (
            "over25_model_v2_candidate.joblib"
        ),
        "production_version": (
            "logistic_regression_over25_v1"
        ),
        "candidate_version": (
            "logistic_regression_over25_v2_candidate"
        ),
        "status": (
            "RESEARCH"
        ),
    },

    "BTTS": {
        "production": (
            "btts_model.joblib"
        ),
        "candidate": (
            "btts_model_v2_candidate.joblib"
        ),
        "production_version": (
            "logistic_regression_btts_v1"
        ),
        "candidate_version": (
            "logistic_regression_btts_v2_candidate"
        ),
        "status": (
            "DISABLED"
        ),
    },
}


def get_market_model_info(
    market_code: str,
):

    return (
        MARKET_MODEL_REGISTRY.get(
            market_code
        )
    )