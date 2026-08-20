from datetime import (
    datetime,
    timezone,
)

from app.database.database import (
    SessionLocal,
)

from app.models.market_consensus_snapshot import (
    MarketConsensusSnapshot,
)

from app.models.match import Match

from app.services.market_consensus_service import (
    calculate_full_market_consensus,
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

    created = 0

    try:

        matches = (
            db.query(Match)
            .filter(
                Match.match_date
                > now
            )
            .order_by(
                Match.match_date.asc()
            )
            .all()
        )

        print()
        print("=" * 100)
        print(
            "ANALITIKO MARKET CONSENSUS SNAPSHOT"
        )
        print("=" * 100)

        print(
            f"Upcoming matches: "
            f"{len(matches)}"
        )

        for match in matches:

            for market_code in MARKETS:

                result = (
                    calculate_full_market_consensus(
                        db=db,
                        match_id=(
                            match.id
                        ),
                        market_code=(
                            market_code
                        ),
                        snapshot_at=now,
                    )
                )

                if not result:
                    continue

                market = (
                    result[
                        "market"
                    ]
                )

                for (
                    selection,
                    data,
                ) in (
                    result[
                        "selections"
                    ].items()
                ):

                    db.add(
                        MarketConsensusSnapshot(
                            match_id=(
                                match.id
                            ),

                            market_id=(
                                market.id
                            ),

                            selection=(
                                selection
                            ),

                            bookmaker_count=(
                                data[
                                    "bookmaker_count"
                                ]
                            ),

                            best_odds=(
                                data[
                                    "best_odds"
                                ]
                            ),

                            median_odds=(
                                data[
                                    "median_odds"
                                ]
                            ),

                            mean_odds=(
                                data[
                                    "mean_odds"
                                ]
                            ),

                            min_odds=(
                                data[
                                    "min_odds"
                                ]
                            ),

                            max_odds=(
                                data[
                                    "max_odds"
                                ]
                            ),

                            raw_implied_probability=(
                                data[
                                    "raw_implied_probability"
                                ]
                            ),

                            consensus_probability=(
                                data[
                                    "consensus_probability"
                                ]
                            ),

                            odds_dispersion=(
                                data[
                                    "odds_dispersion"
                                ]
                            ),

                            opening_odds=(
                                data[
                                    "opening_odds"
                                ]
                            ),

                            current_odds=(
                                data[
                                    "current_odds"
                                ]
                            ),

                            odds_change_pct=(
                                data[
                                    "odds_change_pct"
                                ]
                            ),

                            snapshot_at=now,
                        )
                    )

                    created += 1

        db.commit()

        print(
            f"Snapshots created: "
            f"{created}"
        )

        print()
        print(
            "STATUS: OK"
        )

        print("=" * 100)

    except Exception:

        db.rollback()
        raise

    finally:

        db.close()


if __name__ == "__main__":
    run()