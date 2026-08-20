import truststore

truststore.inject_into_ssl()

import requests

from app.config import (
    API_FOOTBALL_KEY,
    API_FOOTBALL_BASE_URL,
)


class APIFootballClient:

    def __init__(self):
        if not API_FOOTBALL_KEY:
            raise ValueError(
                "API_FOOTBALL_KEY is missing from .env"
            )

        self.base_url = API_FOOTBALL_BASE_URL

        self.headers = {
            "x-apisports-key": API_FOOTBALL_KEY,
        }

    def get(
        self,
        endpoint: str,
        params: dict | None = None,
    ) -> dict:

        url = f"{self.base_url}/{endpoint}"

        response = requests.get(
            url,
            headers=self.headers,
            params=params,
            timeout=30,
        )
        if response.status_code == 429:
            print(
                "API-Football rate limit reached. "
                "Stopping request."
            )

            return {
                "get": "",
                "parameters": [],
                "errors": {
                    "rateLimit":
                        "Too many requests"
                },
                "results": 0,
                "paging": {
                    "current": 1,
                    "total": 1,
                },
                "response": [],
            }

        response.raise_for_status()

        data = response.json()

        # API-Football sometimes returns HTTP 200
        # but includes errors inside the JSON response.
        errors = data.get("errors")

        if errors:
            print(
                f"API-Football warning/error "
                f"for {endpoint}: {errors}"
            )

        return data

    # ============================================================
    # FIXTURES
    # ============================================================

    def get_fixtures_by_date(
        self,
        date: str,
    ) -> dict:

        return self.get(
            "fixtures",
            params={
                "date": date,
            },
        )

    def get_fixtures_by_date_and_league(
        self,
        date: str,
        league_id: int,
        season: int,
    ) -> dict:

        return self.get(
            "fixtures",
            params={
                "date": date,
                "league": league_id,
                "season": season,
            },
        )

    def get_fixture(
        self,
        fixture_id: int,
    ) -> dict:

        return self.get(
            "fixtures",
            params={
                "id": fixture_id,
            },
        )

    # ============================================================
    # RECENT TEAM FIXTURES
    # ============================================================

    def get_team_recent_fixtures(
        self,
        team_id: int,
        last: int = 5,
    ) -> dict:

        return self.get(
            "fixtures",
            params={
                "team": team_id,
                "last": last,
                "status": "FT-AET-PEN",
            },
        )

    # ============================================================
    # FIXTURE STATISTICS
    # ============================================================

    def get_fixture_statistics(
        self,
        fixture_id: int,
    ) -> dict:

        return self.get(
            "fixtures/statistics",
            params={
                "fixture": fixture_id,
            },
        )

    # ============================================================
    # TEAM STATISTICS
    # ============================================================

    def get_team_statistics(
        self,
        league_id: int,
        season: int,
        team_id: int,
    ) -> dict:

        return self.get(
            "teams/statistics",
            params={
                "league": league_id,
                "season": season,
                "team": team_id,
            },
        )

    # ============================================================
    # ODDS
    # ============================================================

    def get_odds_by_fixture(
            self,
            fixture_id: int,
    ) -> dict:

        return self.get(
            "odds",
            params={
                "fixture": fixture_id,
            },
        )

    def get_odds_bets(
            self,
    ) -> dict:

        return self.get(
            "odds/bets"
        )

    def get_odds_by_fixture_and_bet(
            self,
            fixture_id: int,
            bet_id: int,
    ) -> dict:

        return self.get(
            "odds",
            params={
                "fixture":
                    fixture_id,

                "bet":
                    bet_id,
            },
        )
    # ============================================================
    # HEAD TO HEAD
    # ============================================================

    def get_head_to_head(
        self,
        home_team_id: int,
        away_team_id: int,
        last: int = 10,
    ) -> dict:

        return self.get(
            "fixtures/headtohead",
            params={
                "h2h": (
                    f"{home_team_id}-"
                    f"{away_team_id}"
                ),
                "last": last,
            },
        )

    # ============================================================
    # API-FOOTBALL PREDICTIONS
    # ============================================================

    def get_prediction(
        self,
        fixture_id: int,
    ) -> dict:

        return self.get(
            "predictions",
            params={
                "fixture": fixture_id,
            },
        )

    # ============================================================
    # LEAGUES
    # ============================================================

    def get_leagues(
        self,
        country: str | None = None,
    ) -> dict:

        params = {}

        if country:
            params["country"] = country

        return self.get(
            "leagues",
            params=params,
        )

    # ============================================================
    # STANDINGS
    # ============================================================

    def get_standings(
        self,
        league_id: int,
        season: int,
    ) -> dict:

        return self.get(
            "standings",
            params={
                "league": league_id,
                "season": season,
            },
        )

    # ============================================================
    # INJURIES
    # ============================================================

    def get_fixture_injuries(
        self,
        fixture_id: int,
    ) -> dict:

        return self.get(
            "injuries",
            params={
                "fixture": fixture_id,
            },
        )

    def get_team_fixtures_by_date_range(
            self,
            team_id: int,
            date_from: str,
            date_to: str,
            season: int = 2024,
    ):
        return self.get(
            "fixtures",
            params={
                "team": team_id,
                "season": season,
                "from": date_from,
                "to": date_to,
            },
        )

    def get_league_fixtures(
            self,
            league_id: int,
            season: int,
    ):
        return self.get(
            "fixtures",
            params={
                "league": league_id,
                "season": season,
            },
        )

    def get_team_fixtures_by_season(
            self,
            team_id: int,
            season: int,
    ):

        return self.get(
            "fixtures",
            params={
                "team":
                    team_id,

                "season":
                    season,
            },
        )