def calculate_form_score(fixtures: list[dict], team_id: int) -> float:
    if not fixtures:
        return 0.0

    points = 0

    for item in fixtures:
        goals = item.get("goals", {})

        home = item["teams"]["home"]
        away = item["teams"]["away"]

        home_goals = goals.get("home")
        away_goals = goals.get("away")

        if home_goals is None or away_goals is None:
            continue

        if home["id"] == team_id:
            team_goals = home_goals
            opponent_goals = away_goals
        else:
            team_goals = away_goals
            opponent_goals = home_goals

        if team_goals > opponent_goals:
            points += 3
        elif team_goals == opponent_goals:
            points += 1

    max_points = len(fixtures) * 3

    if max_points == 0:
        return 0.0

    return round((points / max_points) * 10, 1)

def parse_team_statistics(data: dict) -> dict | None:
    response = data.get("response")

    if not response:
        return None

    goals = response.get("goals", {})

    goals_for = (
        goals
        .get("for", {})
        .get("average", {})
        .get("total")
    )

    goals_against = (
        goals
        .get("against", {})
        .get("average", {})
        .get("total")
    )

    fixtures = response.get(
        "fixtures",
        {}
    )

    played = (
        fixtures
        .get("played", {})
        .get("total", 0)
    )

    return {
        "goals_for_avg": float(goals_for or 0),
        "goals_against_avg": float(goals_against or 0),
        "played": played,
    }

