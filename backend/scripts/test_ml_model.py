from app.ml.ml_predictor import (
    predict_result,
)


def run():

    result = predict_result(
        league="La Liga",

        home_form=6.5,
        away_form=4.5,

        home_goals_avg=1.6,
        away_goals_avg=1.1,

        home_goals_against_avg=1.0,
        away_goals_against_avg=1.5,

        home_xg=1.5,
        away_xg=1.1,

        h2h_home_score=6.5,
        h2h_away_score=3.5,
        h2h_matches=5,
    )

    print()
    print("=" * 60)
    print("ANALITIKO ML TEST")
    print("=" * 60)

    print(
        f"Pick: "
        f"{result['pick']}"
    )

    print()

    print(
        "Probabilities:"
    )

    print(
        f"HOME: "
        f"{result['probabilities']['HOME']}%"
    )

    print(
        f"DRAW: "
        f"{result['probabilities']['DRAW']}%"
    )

    print(
        f"AWAY: "
        f"{result['probabilities']['AWAY']}%"
    )

    print()

    print(
        f"Confidence: "
        f"{result['confidence']}%"
    )

    print(
        f"Margin: "
        f"{result['margin']}%"
    )

    print(
        f"Analitiko score: "
        f"{result['analitiko_score']}"
    )

    print(
        f"League threshold: "
        f"{result['league_threshold']}"
    )

    print(
        f"Strong pick: "
        f"{result['is_strong_pick']}"
    )

    print(
        f"Confidence level: "
        f"{result['confidence_level']}"
    )

    print()

    print(
        f"Classes: "
        f"{result['trained_classes']}"
    )

    print(
        f"Experimental: "
        f"{result['experimental']}"
    )

    print("=" * 60)


if __name__ == "__main__":
    run()