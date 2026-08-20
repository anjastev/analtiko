from app.models.h2h import H2HMatch


def calculate_h2h_summary(
    matches: list[H2HMatch],
    home_team_external_id: int,
) -> dict:

    if not matches:
        return {
            "matches": 0,
            "home_wins": 0,
            "draws": 0,
            "away_wins": 0,
            "home_goals_avg": 0.0,
            "away_goals_avg": 0.0,
        }

    home_wins = 0
    draws = 0
    away_wins = 0

    home_goals_total = 0
    away_goals_total = 0

    for match in matches:

        if (
            match.home_team_external_id
            == home_team_external_id
        ):
            home_goals = match.home_goals
            away_goals = match.away_goals
        else:
            home_goals = match.away_goals
            away_goals = match.home_goals

        home_goals_total += home_goals
        away_goals_total += away_goals

        if home_goals > away_goals:
            home_wins += 1

        elif home_goals < away_goals:
            away_wins += 1

        else:
            draws += 1

    total = len(matches)

    return {
        "matches": total,

        "home_wins":
            home_wins,

        "draws":
            draws,

        "away_wins":
            away_wins,

        "home_goals_avg":
            round(
                home_goals_total / total,
                2,
            ),

        "away_goals_avg":
            round(
                away_goals_total / total,
                2,
            ),
    }


def calculate_h2h_scores(
    matches,
    home_team_external_id: int,
) -> dict:
    """
    Converts historical H2H matches
    into two scores between 0 and 10.

    Win  = 3 points
    Draw = 1 point
    Loss = 0 points
    """

    if not matches:
        return {
            "home_score": 5.0,
            "away_score": 5.0,
        }

    home_points = 0
    away_points = 0

    for match in matches:

        if (
            match.home_team_external_id
            == home_team_external_id
        ):
            home_goals = (
                match.home_goals
            )

            away_goals = (
                match.away_goals
            )

        else:
            home_goals = (
                match.away_goals
            )

            away_goals = (
                match.home_goals
            )

        if home_goals > away_goals:
            home_points += 3

        elif away_goals > home_goals:
            away_points += 3

        else:
            home_points += 1
            away_points += 1

    max_points = (
        len(matches) * 3
    )

    if max_points == 0:
        return {
            "home_score": 5.0,
            "away_score": 5.0,
        }

    home_score = (
        home_points
        / max_points
    ) * 10

    away_score = (
        away_points
        / max_points
    ) * 10

    return {
        "home_score": round(
            home_score,
            1,
        ),

        "away_score": round(
            away_score,
            1,
        ),
    }

