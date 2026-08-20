from datetime import (
    datetime,
    timezone,
)

from app.database.database import (
    SessionLocal,
)

from app.models.intelligence_feature_snapshot import (
    IntelligenceFeatureSnapshot,
)

from app.models.market_consensus_snapshot import (
    MarketConsensusSnapshot,
)

from app.models.match import Match

from app.models.team_power_rating import (
    TeamPowerRating,
)


def run():

    db = SessionLocal()

    now = datetime.now(
        timezone.utc
    )

    db_now = (
        now.replace(
            tzinfo=None
        )
    )

    try:

        power_rows = (
            db.query(
                TeamPowerRating
            )
            .count()
        )

        consensus_rows = (
            db.query(
                MarketConsensusSnapshot
            )
            .count()
        )

        feature_rows = (
            db.query(
                IntelligenceFeatureSnapshot
            )
            .count()
        )

        upcoming = (
            db.query(Match)
            .filter(
                Match.match_date
                > db_now
            )
            .count()
        )

        feature_matches = (
            db.query(
                IntelligenceFeatureSnapshot.match_id
            )
            .join(
                Match,
                Match.id
                == IntelligenceFeatureSnapshot.match_id,
            )
            .filter(
                Match.match_date
                > db_now
            )
            .distinct()
            .count()
        )

        coverage = (
            feature_matches
            / upcoming
            * 100.0
            if upcoming
            else 0.0
        )

        market_feature_matches = (
            db.query(
                IntelligenceFeatureSnapshot.match_id
            )
            .join(
                Match,
                Match.id
                == IntelligenceFeatureSnapshot.match_id,
            )
            .filter(
                Match.match_date
                > db_now,

                IntelligenceFeatureSnapshot
                .home_market_probability
                .isnot(None),

                IntelligenceFeatureSnapshot
                .draw_market_probability
                .isnot(None),

                IntelligenceFeatureSnapshot
                .away_market_probability
                .isnot(None),
            )
            .distinct()
            .count()
        )

        print()
        print("=" * 100)
        print(
            "ANALITIKO INTELLIGENCE V2 AUDIT"
        )
        print("=" * 100)

        print(
            f"Elo rows: "
            f"{power_rows}"
        )

        print(
            f"Consensus snapshots: "
            f"{consensus_rows}"
        )

        print(
            f"Feature snapshots: "
            f"{feature_rows}"
        )

        print(
            f"Upcoming matches: "
            f"{upcoming}"
        )

        print(
            f"Feature-ready matches: "
            f"{feature_matches}"
        )

        print(
            f"Feature coverage: "
            f"{coverage:.1f}%"
        )

        print(
            f"With 1X2 market features: "
            f"{market_feature_matches}"
        )

        print()

        if (
            feature_matches > 0
            and
            consensus_rows > 0
        ):

            print(
                "STATUS: OK"
            )

        else:

            print(
                "STATUS: PARTIAL"
            )

        print("=" * 100)

    finally:

        db.close()


if __name__ == "__main__":
    run()