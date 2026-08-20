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
MARKET_CODE = "DC"

MAX_FIXTURES = 100


FINISHED_STATUSES = {
    "FT",
    "AET",
    "PEN",
}


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


def find_double_chance_bets(
    client,
):

    data = (
        client.get_odds_bets()
    )

    if data.get("errors"):

        raise RuntimeError(
            f"Odds bets error: "
            f"{data.get('errors')}"
        )

    candidates = []

    for row in data.get(
        "response",
        []
    ):

        name = str(
            row.get(
                "name",
                ""
            )
        )

        normalized = (
            normalize_text(
                name
            )
        )

        if (
            "double chance"
            in normalized
        ):

            candidates.append(
                {
                    "id":
                        row.get(
                            "id"
                        ),

                    "name":
                        name,
                }
            )

    return candidates


def map_dc_selection(
    value,
):

    raw = (
        normalize_text(
            value
        )
    )

    compact = (
        raw
        .replace(
            " ",
            ""
        )
        .replace(
            "-",
            ""
        )
        .replace(
            "/",
            ""
        )
        .replace(
            "_",
            ""
        )
    )

    # 1X
    if compact in {
        "1x",
        "x1",
        "homedraw",
        "drawhome",
        "homeordraw",
        "draworhome",
        "1orx",
        "xor1",
    }:

        return "1X"

    # X2
    if compact in {
        "x2",
        "2x",
        "drawaway",
        "awaydraw",
        "draworaway",
        "awayordraw",
        "xor2",
        "2orx",
    }:

        return "X2"

    # 12
    if compact in {
        "12",
        "21",
        "homeaway",
        "awayhome",
        "homeoraway",
        "awayorhome",
        "1or2",
        "2or1",
    }:

        return "12"

    # Defensive contains logic.

    if (
        "home"
        in raw
        and
        "draw"
        in raw
    ):

        return "1X"

    if (
        "away"
        in raw
        and
        "draw"
        in raw
    ):

        return "X2"

    if (
        "home"
        in raw
        and
        "away"
        in raw
    ):

        return "12"

    return None


def parse_odds(
    value,
):

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


def row_exists(
    db,
    *,
    match_id,
    market_id,
    bookmaker,
    selection,
    odds,
    source,
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

            MarketOdds.bookmaker
            == bookmaker,

            MarketOdds.selection
            == selection,

            MarketOdds.odds
            == odds,

            MarketOdds.source
            == source,
        )
        .first()
        is not None
    )


def run():

    db = SessionLocal()

    client = (
        APIFootballClient()
    )

    now = datetime.now(
        timezone.utc
    )

    created = 0
    duplicate = 0
    fixtures_with_dc = 0
    fixtures_without_dc = 0

    recognized = 0
    unrecognized = 0

    raw_values_seen = set()

    try:

        market = (
            db.query(Market)
            .filter(
                Market.sport
                == SPORT,

                Market.code
                == MARKET_CODE,
            )
            .first()
        )

        if market is None:

            raise RuntimeError(
                "DC market does not exist."
            )

        candidates = (
            find_double_chance_bets(
                client
            )
        )

        print()
        print("=" * 100)
        print(
            "ANALITIKO DIRECT DOUBLE CHANCE SYNC"
        )
        print("=" * 100)

        if not candidates:

            print(
                "No Double Chance bet "
                "definition found."
            )

            print(
                "STATUS: BLOCKED"
            )

            return

        print(
            "Double Chance bet definitions:"
        )

        for candidate in candidates:

            print(
                f"  "
                f"{candidate['id']} | "
                f"{candidate['name']}"
            )

        # Usually only one canonical Double Chance bet.
        bet_id = (
            candidates[0][
                "id"
            ]
        )

        print()
        print(
            f"Using bet ID: "
            f"{bet_id}"
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

        print(
            f"Upcoming fixtures: "
            f"{len(matches)}"
        )

        for match in matches:

            fixture_id = (
                match.external_id
            )

            if not fixture_id:
                continue

            print()
            print("-" * 100)

            print(
                f"{match.home_team.name} "
                f"vs "
                f"{match.away_team.name}"
            )

            data = (
                client
                .get_odds_by_fixture_and_bet(
                    fixture_id=int(
                        fixture_id
                    ),
                    bet_id=int(
                        bet_id
                    ),
                )
            )

            if data.get(
                "errors"
            ):

                print(
                    f"API errors: "
                    f"{data['errors']}"
                )

                fixtures_without_dc += 1

                continue

            response = (
                data.get(
                    "response",
                    []
                )
            )

            fixture_rows = 0

            for item in response:

                for bookmaker in (
                    item.get(
                        "bookmakers",
                        []
                    )
                ):

                    bookmaker_name = (
                        str(
                            bookmaker.get(
                                "name",
                                "UNKNOWN",
                            )
                        )
                    )

                    for bet in (
                        bookmaker.get(
                            "bets",
                            []
                        )
                    ):

                        print_name = str(
                            bet.get(
                                "name",
                                ""
                            )
                        )

                        for value in (
                            bet.get(
                                "values",
                                []
                            )
                        ):

                            raw_value = (
                                value.get(
                                    "value"
                                )
                            )

                            raw_values_seen.add(
                                str(
                                    raw_value
                                )
                            )

                            selection = (
                                map_dc_selection(
                                    raw_value
                                )
                            )

                            if selection is None:

                                unrecognized += 1

                                print(
                                    f"[UNMAPPED] "
                                    f"{print_name} | "
                                    f"{raw_value}"
                                )

                                continue

                            odds = (
                                parse_odds(
                                    value.get(
                                        "odd"
                                    )
                                )
                            )

                            if odds is None:
                                continue

                            recognized += 1

                            source = (
                                "api_football_dc"
                            )

                            if (
                                row_exists(
                                    db=db,

                                    match_id=(
                                        match.id
                                    ),

                                    market_id=(
                                        market.id
                                    ),

                                    bookmaker=(
                                        bookmaker_name
                                    ),

                                    selection=(
                                        selection
                                    ),

                                    odds=(
                                        odds
                                    ),

                                    source=(
                                        source
                                    ),
                                )
                            ):

                                duplicate += 1
                                continue

                            db.add(
                                MarketOdds(
                                    match_id=(
                                        match.id
                                    ),

                                    market_id=(
                                        market.id
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

                                    source=(
                                        source
                                    ),

                                    recorded_at=(
                                        datetime.now(
                                            timezone.utc
                                        )
                                    ),
                                )
                            )

                            created += 1
                            fixture_rows += 1

            db.commit()

            if fixture_rows > 0:

                fixtures_with_dc += 1

                print(
                    f"DC odds created: "
                    f"{fixture_rows}"
                )

            else:

                fixtures_without_dc += 1

                print(
                    "No direct DC odds."
                )

        print()
        print("=" * 100)
        print(
            "DOUBLE CHANCE SYNC SUMMARY"
        )
        print("=" * 100)

        print(
            f"Fixtures with DC:      "
            f"{fixtures_with_dc}"
        )

        print(
            f"Fixtures without DC:   "
            f"{fixtures_without_dc}"
        )

        print(
            f"Recognized values:     "
            f"{recognized}"
        )

        print(
            f"Unrecognized values:   "
            f"{unrecognized}"
        )

        print(
            f"Rows created:          "
            f"{created}"
        )

        print(
            f"Duplicates:             "
            f"{duplicate}"
        )

        print()
        print(
            "Raw DC values seen:"
        )

        for value in sorted(
            raw_values_seen
        ):

            print(
                f"  {value}"
            )

        print()

        if fixtures_with_dc > 0:

            print(
                "STATUS: OK"
            )

        else:

            print(
                "STATUS: NO DIRECT DC"
            )

        print("=" * 100)

    except Exception:

        db.rollback()
        raise

    finally:

        db.close()


if __name__ == "__main__":
    run()