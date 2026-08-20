from app.collectors.api_football import (
    APIFootballClient,
)

from app.database.database import (
    SessionLocal,
)

from app.models.match import Match


def run():
    db = SessionLocal()
    client = APIFootballClient()

    try:
        match = (
            db.query(Match)
            .order_by(
                Match.match_date.asc()
            )
            .first()
        )

        if not match:
            print("No match found.")
            return

        teams = [
            match.home_team,
            match.away_team,
        ]

        for team in teams:
            print()
            print("=" * 60)
            print(team.name)
            print(
                "External ID:",
                team.external_id,
            )

            data = (
                client.get_team_recent_fixtures(
                    team_id=team.external_id,
                    last=5,
                )
            )

            print(
                "Errors:",
                data.get("errors"),
            )

            print(
                "Results:",
                data.get("results"),
            )

            fixtures = data.get(
                "response",
                [],
            )

            print(
                "Fixtures returned:",
                len(fixtures),
            )

            for item in fixtures:
                fixture = item["fixture"]
                teams_data = item["teams"]
                goals = item["goals"]

                print(
                    fixture["id"],
                    "|",
                    fixture["status"]["short"],
                    "|",
                    teams_data["home"]["name"],
                    goals["home"],
                    "-",
                    goals["away"],
                    teams_data["away"]["name"],
                )

    finally:
        db.close()


if __name__ == "__main__":
    run()