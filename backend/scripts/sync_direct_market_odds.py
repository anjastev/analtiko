from __future__ import annotations

from datetime import (
    datetime,
    timezone,
)

from app.collectors.api_football import (
    APIFootballClient,
)

from app.database.database import (
    SessionLocal,
)

from app.models.market import Market
from app.models.market_odds import (
    MarketOdds,
)
from app.models.match import Match


SPORT = "football"

MAX_FIXTURES = 100


FINISHED_STATUSES = {
    "FT",
    "AET",
    "PEN",
}


# ============================================================
# MARKET NAME ALIASES
# ============================================================

MATCH_WINNER_NAMES = {
    "match winner",
    "1x2",
    "fulltime result",
    "full time result",
}


DOUBLE_CHANCE_NAMES = {
    "double chance",
}


BTTS_NAMES = {
    "both teams score",
    "both teams to score",
}


OU_NAMES = {
    "goals over/under",
    "goals over under",
    "over/under",
    "total goals",
}


# ============================================================
# HELPERS
# ============================================================

def now_utc():

    return datetime.now(
        timezone.utc
    )


def normalize_text(
    value,
):

    if value is None:
        return ""

    return (
        str(value)
        .strip()
        .lower()
    )


def parse_decimal_odds(
    value,
):

    if value is None:
        return None

    try:

        odds = float(
            value
        )

    except (
        TypeError,
        ValueError,
    ):

        return None

    if odds <= 1.0:
        return None

    return odds


def get_market_map(
    db,
):

    markets = (
        db.query(Market)
        .filter(
            Market.sport
            == SPORT,

            Market.code.in_(
                [
                    "1X2",
                    "DC",
                    "OU_25",
                    "BTTS",
                ]
            ),
        )
        .all()
    )

    return {
        market.code:
            market
        for market in markets
    }


def map_match_winner_selection(
    value: str,
):

    normalized = (
        normalize_text(
            value
        )
    )

    if normalized in {
        "home",
        "1",
    }:
        return "HOME"

    if normalized in {
        "draw",
        "x",
    }:
        return "DRAW"

    if normalized in {
        "away",
        "2",
    }:
        return "AWAY"

    return None


def map_double_chance_selection(
    value: str,
):

    normalized = (
        normalize_text(
            value
        )
        .replace(
            " ",
            ""
        )
    )

    aliases = {
        "1x": "1X",
        "x1": "1X",

        "x2": "X2",
        "2x": "X2",

        "12": "12",
        "1or2": "12",
        "homeoraway": "12",

        "homeordraw": "1X",
        "draworhome": "1X",

        "draworaway": "X2",
        "awayordraw": "X2",
    }

    return aliases.get(
        normalized
    )


def map_btts_selection(
    value: str,
):

    normalized = (
        normalize_text(
            value
        )
    )

    if normalized in {
        "yes",
        "y",
    }:
        return "YES"

    if normalized in {
        "no",
        "n",
    }:
        return "NO"

    return None


def map_ou25_selection(
    value: str,
):

    normalized = (
        normalize_text(
            value
        )
        .replace(
            " ",
            ""
        )
    )

    if (
        "over" in normalized
        and
        "2.5" in normalized
    ):
        return "OVER"

    if (
        "under" in normalized
        and
        "2.5" in normalized
    ):
        return "UNDER"

    return None


def identify_market_code(
    bet_name: str,
):

    normalized = (
        normalize_text(
            bet_name
        )
    )

    if normalized in MATCH_WINNER_NAMES:
        return "1X2"

    if normalized in DOUBLE_CHANCE_NAMES:
        return "DC"

    if normalized in BTTS_NAMES:
        return "BTTS"

    if normalized in OU_NAMES:
        return "OU_25"

    # Defensive fuzzy matching.

    if (
        "double"
        in normalized
        and
        "chance"
        in normalized
    ):
        return "DC"

    if (
        "both teams"
        in normalized
        and
        "score"
        in normalized
    ):
        return "BTTS"

    if (
        "match winner"
        in normalized
    ):
        return "1X2"

    if (
        "goal"
        in normalized
        and
        (
            "over"
            in normalized
            or
            "under"
            in normalized
        )
    ):
        return "OU_25"

    return None


def map_selection(
    market_code: str,
    value: str,
):

    if market_code == "1X2":

        return (
            map_match_winner_selection(
                value
            )
        )

    if market_code == "DC":

        return (
            map_double_chance_selection(
                value
            )
        )

    if market_code == "BTTS":

        return (
            map_btts_selection(
                value
            )
        )

    if market_code == "OU_25":

        return (
            map_ou25_selection(
                value
            )
        )

    return None


def odds_row_exists(
    db,
    *,
    match_id: int,
    market_id: int,
    selection: str,
    bookmaker: str,
    odds: float,
    recorded_at,
):

    return (
        db.query(
            MarketOdds
        )
        .filter(
            MarketOdds.match_id
            == match_id,

            MarketOdds.market_id
            == market_id,

            MarketOdds.selection
            == selection,

            MarketOdds.bookmaker
            == bookmaker,

            MarketOdds.odds
            == odds,

            MarketOdds.recorded_at
            == recorded_at,
        )
        .first()
        is not None
    )


def save_market_odds(
    db,
    *,
    match_id: int,
    market,
    selection: str,
    bookmaker: str,
    odds: float,
    recorded_at,
):

    if odds_row_exists(
        db=db,
        match_id=match_id,
        market_id=market.id,
        selection=selection,
        bookmaker=bookmaker,
        odds=odds,
        recorded_at=recorded_at,
    ):

        return False

    row = (
        MarketOdds(
            match_id=(
                match_id
            ),

            market_id=(
                market.id
            ),

            selection=(
                selection
            ),

            bookmaker=(
                bookmaker
            ),

            odds=(
                odds
            ),

            source=(
                "api_football"
            ),

            recorded_at=(
                recorded_at
            ),
        )
    )

    db.add(
        row
    )

    return True


# ============================================================
# MAIN
# ============================================================

def run():

    db = SessionLocal()

    client = (
        APIFootballClient()
    )

    now = now_utc()

    created = 0
    unchanged = 0
    fixtures_checked = 0

    bookmakers_seen = 0
    bets_seen = 0
    values_seen = 0

    recognized_values = 0
    unsupported_bets = 0
    invalid_values = 0

    api_errors = 0

    try:

        market_map = (
            get_market_map(
                db
            )
        )

        required_markets = {
            "1X2",
            "DC",
            "OU_25",
            "BTTS",
        }

        missing_markets = (
            required_markets
            - set(
                market_map.keys()
            )
        )

        if missing_markets:

            raise RuntimeError(
                f"Missing markets: "
                f"{sorted(missing_markets)}"
            )

        matches = (
            db.query(Match)
            .filter(
                Match.match_date
                >= now,

                ~Match.status.in_(
                    FINISHED_STATUSES
                ),
            )
            .order_by(
                Match.match_date.asc()
            )
            .limit(
                MAX_FIXTURES
            )
            .all()
        )

        print()
        print("=" * 100)
        print(
            "ANALITIKO DIRECT MARKET ODDS SYNC"
        )
        print("=" * 100)

        print(
            f"Upcoming fixtures: "
            f"{len(matches)}"
        )

        for match in matches:

            fixture_external_id = (
                match.external_id
            )

            if not fixture_external_id:

                print()
                print(
                    f"[SKIP] "
                    f"{match.home_team.name} "
                    f"vs "
                    f"{match.away_team.name} "
                    f"- missing external_id"
                )

                continue

            fixtures_checked += 1

            print()
            print("-" * 100)

            print(
                f"[{match.id}] "
                f"{match.home_team.name} "
                f"vs "
                f"{match.away_team.name}"
            )

            print(
                f"Fixture external ID: "
                f"{fixture_external_id}"
            )

            try:

                data = (
                    client.get_odds_by_fixture(
                        int(
                            fixture_external_id
                        )
                    )
                )

            except Exception as error:

                api_errors += 1

                print(
                    f"API FAILED: "
                    f"{error}"
                )

                continue

            errors = (
                data.get(
                    "errors"
                )
            )

            if errors:

                api_errors += 1

                print(
                    f"API errors: "
                    f"{errors}"
                )

                continue

            responses = (
                data.get(
                    "response",
                    []
                )
            )

            if not responses:

                print(
                    "No pre-match odds returned."
                )

                continue

            fixture_created = 0

            for response_item in responses:

                bookmakers = (
                    response_item.get(
                        "bookmakers",
                        []
                    )
                )

                for bookmaker in bookmakers:

                    bookmakers_seen += 1

                    bookmaker_name = str(
                        bookmaker.get(
                            "name",
                            "UNKNOWN",
                        )
                    )

                    bets = (
                        bookmaker.get(
                            "bets",
                            []
                        )
                    )

                    for bet in bets:

                        bets_seen += 1

                        bet_name = str(
                            bet.get(
                                "name",
                                ""
                            )
                        )

                        market_code = (
                            identify_market_code(
                                bet_name
                            )
                        )

                        if market_code is None:

                            unsupported_bets += 1
                            continue

                        market = (
                            market_map[
                                market_code
                            ]
                        )

                        values = (
                            bet.get(
                                "values",
                                []
                            )
                        )

                        for value_row in values:

                            values_seen += 1

                            raw_value = (
                                value_row.get(
                                    "value"
                                )
                            )

                            selection = (
                                map_selection(
                                    market_code,
                                    raw_value,
                                )
                            )

                            if selection is None:

                                invalid_values += 1
                                continue

                            odds = (
                                parse_decimal_odds(
                                    value_row.get(
                                        "odd"
                                    )
                                )
                            )

                            if odds is None:

                                invalid_values += 1
                                continue

                            recognized_values += 1

                            # We record the time WE saw the price.
                            #
                            # This is safer than pretending the
                            # provider gives an exact quote timestamp
                            # for every bookmaker/value.
                            recorded_at = (
                                now_utc()
                            )

                            saved = (
                                save_market_odds(
                                    db=db,

                                    match_id=(
                                        match.id
                                    ),

                                    market=(
                                        market
                                    ),

                                    selection=(
                                        selection
                                    ),

                                    bookmaker=(
                                        bookmaker_name
                                    ),

                                    odds=(
                                        odds
                                    ),

                                    recorded_at=(
                                        recorded_at
                                    ),
                                )
                            )

                            if saved:

                                created += 1
                                fixture_created += 1

                            else:

                                unchanged += 1

            db.commit()

            print(
                f"Normalized odds created: "
                f"{fixture_created}"
            )

        print()
        print("=" * 100)
        print(
            "DIRECT ODDS SYNC SUMMARY"
        )
        print("=" * 100)

        print(
            f"Fixtures checked:        "
            f"{fixtures_checked}"
        )

        print(
            f"Bookmakers seen:         "
            f"{bookmakers_seen}"
        )

        print(
            f"Bets seen:               "
            f"{bets_seen}"
        )

        print(
            f"Values seen:             "
            f"{values_seen}"
        )

        print(
            f"Recognized values:       "
            f"{recognized_values}"
        )

        print(
            f"Odds rows created:       "
            f"{created}"
        )

        print(
            f"Unchanged:               "
            f"{unchanged}"
        )

        print(
            f"Unsupported bets:        "
            f"{unsupported_bets}"
        )

        print(
            f"Invalid values:          "
            f"{invalid_values}"
        )

        print(
            f"API errors:              "
            f"{api_errors}"
        )

        print()

        if created > 0:

            print(
                "STATUS: OK"
            )

        elif api_errors > 0:

            print(
                "STATUS: PARTIAL"
            )

        else:

            print(
                "STATUS: NO ODDS"
            )

        print("=" * 100)

    except Exception:

        db.rollback()
        raise

    finally:

        db.close()


if __name__ == "__main__":
    run()