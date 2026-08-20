def clamp(
    value: float,
    minimum: float,
    maximum: float,
) -> float:
    return max(
        minimum,
        min(value, maximum),
    )


def calculate_odds_movement_score(
    opening_home: float,
    current_home: float,
    opening_draw: float,
    current_draw: float,
    opening_away: float,
    current_away: float,
) -> float:

    movements = [
        abs(
            opening_home
            - current_home
        ),
        abs(
            opening_draw
            - current_draw
        ),
        abs(
            opening_away
            - current_away
        ),
    ]

    average_movement = (
        sum(movements)
        / len(movements)
    )

    score = (
        average_movement
        * 120
    )

    return clamp(
        score,
        0,
        100,
    )


def calculate_favorite_drop_score(
    opening_home: float,
    current_home: float,
    opening_away: float,
    current_away: float,
) -> float:
    """
    Measures meaningful odds drop
    on the likely favorite.

    Lower odds = stronger market movement.
    """

    opening_favorite = min(
        opening_home,
        opening_away,
    )

    if opening_favorite == opening_home:
        current_favorite = (
            current_home
        )
    else:
        current_favorite = (
            current_away
        )

    if opening_favorite <= 0:
        return 0.0

    drop_percentage = (
        (
            opening_favorite
            - current_favorite
        )
        / opening_favorite
    ) * 100

    if drop_percentage <= 0:
        return 0.0

    score = (
        drop_percentage
        * 8
    )

    return clamp(
        score,
        0,
        100,
    )


def calculate_form_score(
    home_form: float,
    away_form: float,
) -> float:

    average_form = (
        home_form
        + away_form
    ) / 2

    return clamp(
        average_form * 10,
        0,
        100,
    )


def calculate_goals_score(
    home_goals: float,
    away_goals: float,
) -> float:

    total = (
        home_goals
        + away_goals
    )

    score = (
        total / 5
    ) * 100

    return clamp(
        score,
        0,
        100,
    )


def calculate_xg_score(
    home_xg: float,
    away_xg: float,
) -> float:

    total_xg = (
        home_xg
        + away_xg
    )

    score = (
        total_xg / 5
    ) * 100

    return clamp(
        score,
        0,
        100,
    )


def calculate_h2h_interest_score(
    home_score: float,
    away_score: float,
) -> float:
    """
    Close H2H rivalry gets slightly
    higher interest.

    Very one-sided H2H gets lower score.
    """

    difference = abs(
        home_score
        - away_score
    )

    score = (
        100
        - difference * 8
    )

    return clamp(
        score,
        30,
        100,
    )


def calculate_popularity_score(
    odds_score: float,
    favorite_drop_score: float,
    prediction_confidence: float,
    form_score: float,
    goals_score: float,
    h2h_score: float,
    league_weight: float,
) -> int:

    score = (
        odds_score * 0.25
        + favorite_drop_score * 0.20
        + prediction_confidence * 0.20
        + form_score * 0.10
        + goals_score * 0.10
        + h2h_score * 0.05
        + league_weight * 0.10
    )

    return round(
        clamp(
            score,
            0,
            100,
        )
    )