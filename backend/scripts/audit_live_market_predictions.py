from datetime import (
    datetime,
    timezone,
)

from app.database.database import (
    SessionLocal,
)

from app.models.market import Market
from app.models.market_prediction import (
    MarketPrediction,
)
from app.models.match import Match


MARKETS = [
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

        print()
        print("=" * 80)
        print(
            "ANALITIKO LIVE MARKET PREDICTION AUDIT"
        )
        print("=" * 80)

        for code in MARKETS:

            market = (
                db.query(Market)
                .filter(
                    Market.sport
                    == "football",

                    Market.code
                    == code,
                )
                .first()
            )

            if market is None:

                print(
                    f"[MISSING] {code}"
                )

                continue

            predictions = (
                db.query(
                    MarketPrediction
                )
                .join(
                    Match,
                    Match.id
                    == MarketPrediction.match_id,
                )
                .filter(
                    MarketPrediction.market_id
                    == market.id,

                    Match.match_date
                    >= now,

                    MarketPrediction.actual_result
                    .is_(None),
                )
                .order_by(
                    MarketPrediction.probability
                    .desc()
                )
                .all()
            )

            print()
            print("-" * 80)

            print(
                f"MARKET: "
                f"{code}"
            )

            print(
                f"Predictions: "
                f"{len(predictions)}"
            )

            if not predictions:
                continue

            probabilities = [
                float(
                    item.probability
                )
                for item
                in predictions
            ]

            print(
                f"Min: "
                f"{min(probabilities):.1f}%"
            )

            print(
                f"Average: "
                f"{sum(probabilities) / len(probabilities):.1f}%"
            )

            print(
                f"Max: "
                f"{max(probabilities):.1f}%"
            )

            for threshold in [
                60,
                65,
                70,
                75,
                80,
                85,
            ]:

                count = sum(
                    1
                    for probability
                    in probabilities
                    if probability
                    >= threshold
                )

                print(
                    f">= {threshold}%: "
                    f"{count}"
                )

            print()
            print(
                "TOP PREDICTIONS"
            )

            for prediction in (
                predictions[:10]
            ):

                match = (
                    db.query(Match)
                    .filter(
                        Match.id
                        == prediction.match_id
                    )
                    .first()
                )

                if match is None:
                    continue

                print(
                    f"{match.home_team.name} "
                    f"vs "
                    f"{match.away_team.name}"
                )

                print(
                    f"  {prediction.selection}: "
                    f"{prediction.probability:.1f}%"
                )

        print()
        print("=" * 80)
        print(
            "STATUS: OK"
        )
        print("=" * 80)

    finally:

        db.close()


if __name__ == "__main__":
    run()