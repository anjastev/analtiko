from datetime import (
    datetime,
    timezone,
)

from app.database.database import (
    SessionLocal,
)

from app.models.market import Market
from app.models.market_odds import MarketOdds
from app.models.match import Match

from app.services.market_odds_service import (
    get_latest_odds_per_bookmaker,
    is_odds_fresh,
)


TRACKED_MARKETS = {
    "1X2",
    "DC",
    "OU_25",
    "BTTS",
}


def run():

    db = SessionLocal()

    now = datetime.now(
        timezone.utc
    )

    try:

        markets = (
            db.query(Market)
            .filter(
                Market.sport
                == "football",

                Market.code.in_(
                    TRACKED_MARKETS
                ),
            )
            .all()
        )

        market_map = {
            market.id:
                market
            for market in markets
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

        fresh_rows = 0
        stale_rows = 0

        print()
        print("=" * 100)
        print(
            "ANALITIKO ODDS QUALITY AUDIT"
        )
        print("=" * 100)

        for match in matches:

            has_output = False

            for market in markets:

                selections = (
                    db.query(
                        MarketOdds.selection
                    )
                    .filter(
                        MarketOdds.match_id
                        == match.id,

                        MarketOdds.market_id
                        == market.id,
                    )
                    .distinct()
                    .all()
                )

                if not selections:
                    continue

                if not has_output:

                    print()
                    print(
                        f"{match.home_team.name} "
                        f"vs "
                        f"{match.away_team.name}"
                    )

                    has_output = True

                for (
                    selection,
                ) in selections:

                    rows = (
                        get_latest_odds_per_bookmaker(
                            db=db,
                            match_id=(
                                match.id
                            ),
                            market_code=(
                                market.code
                            ),
                            selection=(
                                selection
                            ),
                            sport="football",
                        )
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

                    stale = (
                        len(rows)
                        - len(fresh)
                    )

                    fresh_rows += len(
                        fresh
                    )

                    stale_rows += (
                        stale
                    )

                    print(
                        f"  "
                        f"{market.code}:"
                        f"{selection} "
                        f"bookmakers="
                        f"{len(rows)} "
                        f"fresh="
                        f"{len(fresh)} "
                        f"stale="
                        f"{stale}"
                    )

        print()
        print("=" * 100)

        print(
            f"Fresh latest bookmaker prices: "
            f"{fresh_rows}"
        )

        print(
            f"Stale latest bookmaker prices: "
            f"{stale_rows}"
        )

        print()

        if fresh_rows > 0:

            print(
                "STATUS: OK"
            )

        else:

            print(
                "STATUS: NO FRESH ODDS"
            )

        print("=" * 100)

    finally:

        db.close()


if __name__ == "__main__":
    run()