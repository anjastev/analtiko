from typing import Any


def parse_number(value: Any) -> float | None:
    if value is None:
        return None

    if isinstance(value, (int, float)):
        return float(value)

    if isinstance(value, str):
        cleaned = value.strip()

        if cleaned.endswith("%"):
            cleaned = cleaned[:-1]

        try:
            return float(cleaned)
        except ValueError:
            return None

    return None


def normalize_stat_name(name: str) -> str:
    return (
        name
        .strip()
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
    )


def get_team_statistics_from_fixture(
    data: dict,
    team_id: int,
) -> dict | None:

    response = data.get("response", [])

    if not response:
        return None

    team_block = None

    for item in response:
        team = item.get("team", {})

        if team.get("id") == team_id:
            team_block = item
            break

    if not team_block:
        return None

    result = {
        "shots": None,
        "corners": None,
        "possession": None,
        "xg": None,
    }

    for stat in team_block.get("statistics", []):
        stat_type = normalize_stat_name(
            stat.get("type", "")
        )

        value = parse_number(
            stat.get("value")
        )

        if stat_type == "total_shots":
            result["shots"] = value

        elif stat_type == "corner_kicks":
            result["corners"] = value

        elif stat_type == "ball_possession":
            result["possession"] = value

        elif stat_type in (
            "expected_goals",
            "expected_goal",
            "xg",
        ):
            result["xg"] = value

    return result


def calculate_average(
    values: list[float],
) -> float:

    if not values:
        return 0.0

    return round(
        sum(values) / len(values),
        2,
    )


def aggregate_team_fixture_stats(
    stats_list: list[dict],
) -> dict:

    shots = []
    corners = []
    possession = []
    xg = []

    for stats in stats_list:

        if stats.get("shots") is not None:
            shots.append(
                stats["shots"]
            )

        if stats.get("corners") is not None:
            corners.append(
                stats["corners"]
            )

        if stats.get("possession") is not None:
            possession.append(
                stats["possession"]
            )

        if stats.get("xg") is not None:
            xg.append(
                stats["xg"]
            )

    return {
        "shots_avg": calculate_average(
            shots
        ),

        "corners_avg": calculate_average(
            corners
        ),

        "possession_avg": calculate_average(
            possession
        ),

        "xg_avg": calculate_average(
            xg
        ),

        "matches_used": max(
            len(shots),
            len(corners),
            len(possession),
            len(xg),
        ),
    }


def get_finished_fixture_ids(
    fixtures: list[dict],
    limit: int = 5,
) -> list[int]:

    finished_statuses = {
        "FT",
        "AET",
        "PEN",
    }

    fixture_ids = []

    for item in fixtures:
        fixture = item.get(
            "fixture",
            {}
        )

        status = (
            fixture
            .get("status", {})
            .get("short")
        )

        fixture_id = fixture.get("id")

        if (
            status in finished_statuses
            and fixture_id
        ):
            fixture_ids.append(
                fixture_id
            )

        if len(fixture_ids) >= limit:
            break

    return fixture_ids


