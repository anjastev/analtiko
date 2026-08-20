from app.models.team_match_history import TeamMatchHistory


def calculate_form_from_history(
    history: list[TeamMatchHistory],
) -> dict:

    if not history:
        return {
            "matches": 0,
            "wins": 0,
            "draws": 0,
            "losses": 0,
            "points": 0,
            "form_score": 0.0,
            "goals_for_avg": 0.0,
            "goals_against_avg": 0.0,
            "sequence": [],
        }

    wins = 0
    draws = 0
    losses = 0

    goals_for = 0
    goals_against = 0

    sequence = []

    for match in history:

        goals_for += match.goals_for
        goals_against += match.goals_against

        if match.result == "W":
            wins += 1
            sequence.append("W")

        elif match.result == "D":
            draws += 1
            sequence.append("D")

        elif match.result == "L":
            losses += 1
            sequence.append("L")

    matches = len(history)

    points = (
        wins * 3
        + draws
    )

    max_points = matches * 3

    form_score = (
        (points / max_points) * 10
        if max_points > 0
        else 0
    )

    return {
        "matches": matches,

        "wins": wins,
        "draws": draws,
        "losses": losses,

        "points": points,

        "form_score": round(
            form_score,
            1,
        ),

        "goals_for_avg": round(
            goals_for / matches,
            2,
        ),

        "goals_against_avg": round(
            goals_against / matches,
            2,
        ),

        "sequence": sequence,
    }