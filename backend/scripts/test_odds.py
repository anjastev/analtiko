from app.collectors.api_football import APIFootballClient
from app.database.database import SessionLocal
from app.models.match import Match

from app.services.odds_parser import (
    parse_odds_response,
)


def run():
    db = SessionLocal()

    client = APIFootballClient()

    try:
        matches = (
            db.query(Match)
            .filter(Match.external_id.isnot(None))
            .order_by(Match.match_date.asc())
            .limit(5)
            .all()
        )

        for match in matches:

            print()
            print(
                match.home_team.name,
                "vs",
                match.away_team.name,
            )

            data = client.get_odds_by_fixture(
                match.external_id
            )

            response = data.get(
                "response",
                [],
            )

            parsed = parse_odds_response(data)

            print(parsed)

            print(
                "Fixture:",
                match.external_id,
            )

            print(
                "Odds found:",
                len(response),
            )

            if response:
                print("SUCCESS")
                break

    finally:
        db.close()


if __name__ == "__main__":
    run()