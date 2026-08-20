from datetime import (
    datetime,
    timezone,
)

from app.database.database import (
    SessionLocal,
)

from app.models.market import Market
from app.models.market_odds import (
    MarketOdds,
)
from app.models.match import Match

from app.services.market_odds_service import (
    is_odds_fresh,
)


MARKETS = [
    "1X2",
    "DC",
    "OU_25",
    "BTTS",
]


def run():

    db = SessionLocal()

    now = datetime.now(
        timezone.utc
    )

    try:

        market_rows = (
            db.query(Market)
            .filter(
                Market.sport
                == "football",

                Market.code.in_(
                    MARKETS
                ),
            )
            .all()
        )

        market_map = {
            market.code:
                market
            for market in market_rows
        }

        matches = (
            db.query(Match)
            .filter(
                Match.match_date
                >= now
            )
            .order_by(
                Match.match_date.asc()
            )
            .all()
        )

        print()
        print("=" * 100)
        print(
            "ANALITIKO DIRECT ODDS COVERAGE"
        )
        print("=" * 100)

        coverage = {
            code: 0
            for code in MARKETS
        }

        for match in matches:

            output = []

            for code in MARKETS:

                market = (
                    market_map.get(
                        code
                    )
                )

                if market is None:
                    continue

                rows = (
                    db.query(
                        MarketOdds
                    )
                    .filter(
                        MarketOdds.match_id
                        == match.id,

                        MarketOdds.market_id
                        == market.id,

                        MarketOdds.source
                        == "api_football",
                    )
                    .all()
                )

                fresh = [
                    row
                    for row in rows
                    if is_odds_fresh(
                        row,
                        reference_time=now,
                        max_age_hours=12,
                    )
                ]

                if fresh:

                    coverage[
                        code
                    ] += 1

                    bookmakers = {
                        row.bookmaker
                        for row in fresh
                    }

                    selections = {
                        row.selection
                        for row in fresh
                    }

                    output.append(
                        f"{code}: "
                        f"{len(bookmakers)} bookies "
                        f"{sorted(selections)}"
                    )

            if output:

                print()
                print(
                    f"{match.home_team.name} "
                    f"vs "
                    f"{match.away_team.name}"
                )

                for line in output:

                    print(
                        f"  {line}"
                    )

        print()
        print("=" * 100)

        print(
            f"Upcoming matches: "
            f"{len(matches)}"
        )

        for code in MARKETS:

            count = (
                coverage[
                    code
                ]
            )

            percentage = (
                count
                / len(matches)
                * 100.0
                if matches
                else 0.0
            )

            print(
                f"{code:<6} "
                f"{count}/"
                f"{len(matches)} "
                f"({percentage:.1f}%)"
            )

        print()
        print(
            "STATUS: OK"
        )

        print("=" * 100)

    finally:

        db.close()


if __name__ == "__main__":
    run()