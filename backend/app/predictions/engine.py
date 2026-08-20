def clamp(
    value: float,
    minimum: float,
    maximum: float,
) -> float:
    return max(
        minimum,
        min(value, maximum),
    )


def normalize_probabilities(
    values: list[float],
) -> list[float]:

    total = sum(values)

    if total <= 0:
        return [
            100 / len(values)
            for _ in values
        ]

    return [
        value / total * 100
        for value in values
    ]


def calculate_match_prediction(
    home_form: float,
    away_form: float,

    home_goals: float,
    away_goals: float,

    home_xg: float,
    away_xg: float,

    home_odds: float,
    draw_odds: float,
    away_odds: float,

    home_h2h_score: float = 5.0,
    away_h2h_score: float = 5.0,
):
    """
    Analitiko prediction engine v2.

    Inputs:
    - recent form: 0-10
    - recent goals per match
    - xG or neutral fallback
    - bookmaker 1/X/2 odds
    - H2H score: 0-10
    """

    # ========================================================
    # TEAM STRENGTH
    # ========================================================

    home_strength = (
        home_form * 0.35
        + home_goals * 1.15
        + home_xg * 1.20
        + home_h2h_score * 0.15
    )

    away_strength = (
        away_form * 0.35
        + away_goals * 1.15
        + away_xg * 1.20
        + away_h2h_score * 0.15
    )

    # Small home advantage
    home_strength += 0.35

    # ========================================================
    # BOOKMAKER IMPLIED PROBABILITIES
    # ========================================================

    odds_home_probability = (
        1 / home_odds
        if home_odds > 0
        else 0
    )

    odds_draw_probability = (
        1 / draw_odds
        if draw_odds > 0
        else 0
    )

    odds_away_probability = (
        1 / away_odds
        if away_odds > 0
        else 0
    )

    market_total = (
        odds_home_probability
        + odds_draw_probability
        + odds_away_probability
    )

    if market_total > 0:
        odds_home_probability /= market_total
        odds_draw_probability /= market_total
        odds_away_probability /= market_total

    # ========================================================
    # RESULT MODEL
    # ========================================================

    home_raw = (
        home_strength
        + odds_home_probability * 6
    )

    away_raw = (
        away_strength
        + odds_away_probability * 6
    )

    strength_difference = abs(
        home_strength
        - away_strength
    )

    draw_raw = (
        4.2
        - strength_difference * 0.35
        + odds_draw_probability * 5
    )

    draw_raw = max(
        draw_raw,
        1,
    )

    (
        home_probability,
        draw_probability,
        away_probability,
    ) = normalize_probabilities(
        [
            home_raw,
            draw_raw,
            away_raw,
        ]
    )

    # ========================================================
    # GOALS MODEL
    # ========================================================

    goals_signal = (
        home_goals
        + away_goals
        + home_xg
        + away_xg
    ) / 2

    over_25 = clamp(
        45
        + (
            goals_signal - 2.5
        ) * 18,
        10,
        90,
    )

    # ========================================================
    # BTTS MODEL
    # ========================================================

    weakest_goal_signal = min(
        home_goals,
        away_goals,
    )

    weakest_xg_signal = min(
        home_xg,
        away_xg,
    )

    btts = clamp(
        38
        + weakest_goal_signal * 11
        + weakest_xg_signal * 7,
        10,
        90,
    )

    # ========================================================
    # MAIN PICK
    # ========================================================

    probabilities = {
        "HOME":
            home_probability,

        "DRAW":
            draw_probability,

        "AWAY":
            away_probability,
    }

    main_pick = max(
        probabilities,
        key=probabilities.get,
    )

    # ========================================================
    # CONFIDENCE
    # ========================================================

    sorted_probs = sorted(
        probabilities.values(),
        reverse=True,
    )

    best_probability = (
        sorted_probs[0]
    )

    second_probability = (
        sorted_probs[1]
    )

    probability_gap = (
        best_probability
        - second_probability
    )

    confidence = clamp(
        45
        + probability_gap * 1.25
        + strength_difference * 2,
        40,
        92,
    )

    return {
        "home_win": round(
            home_probability,
            1,
        ),

        "draw": round(
            draw_probability,
            1,
        ),

        "away_win": round(
            away_probability,
            1,
        ),

        "over_25": round(
            over_25,
            1,
        ),

        "btts_yes": round(
            btts,
            1,
        ),

        "confidence": round(
            confidence,
            1,
        ),

        "main_pick":
            main_pick,
    }