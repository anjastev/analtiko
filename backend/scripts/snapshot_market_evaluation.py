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
from app.models.market_evaluation_snapshot import (
    MarketEvaluationSnapshot,
)
from app.models.match import Match

from app.services.market_policy import (
    get_market_policy,
)


TRACKED_MARKETS = {
    "DC",
    "OU_25",
    "BTTS",
}


def snapshot_exists(
    db,
    prediction_id: int,
):

    return (
        db.query(
            MarketEvaluationSnapshot
        )
        .filter(
            MarketEvaluationSnapshot.prediction_id
            == prediction_id
        )
        .first()
        is not None
    )


def run():

    db = SessionLocal()

    now = datetime.now(
        timezone.utc
    )

    created = 0
    unchanged = 0

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
                .in_(
                    list(
                        market_map.keys()
                    )
                ),

                Match.match_date
                > now,

                MarketPrediction.actual_result
                .is_(None),
            )
            .all()
        )

        print()
        print("=" * 80)
        print(
            "ANALITIKO PROSPECTIVE MARKET SNAPSHOT"
        )
        print("=" * 80)

        print(
            f"Predictions found: "
            f"{len(predictions)}"
        )

        for prediction in predictions:

            if snapshot_exists(
                db=db,
                prediction_id=(
                    prediction.id
                ),
            ):

                unchanged += 1
                continue

            market = (
                market_map[
                    prediction.market_id
                ]
            )

            policy = (
                get_market_policy(
                    market.code
                )
            )

            snapshot = (
                MarketEvaluationSnapshot(
                    match_id=(
                        prediction.match_id
                    ),

                    market_id=(
                        prediction.market_id
                    ),

                    prediction_id=(
                        prediction.id
                    ),

                    market_code=(
                        market.code
                    ),

                    selection=(
                        prediction.selection
                    ),

                    probability=(
                        prediction.probability
                    ),

                    model_version=(
                        prediction.model_version
                    ),

                    market_status=(
                        policy.status
                    ),

                    signal_eligible=(
                        policy.allow_signals
                    ),

                    combination_eligible=(
                        policy.allow_combinations
                    ),
                )
            )

            db.add(
                snapshot
            )

            created += 1

        db.commit()

        print()
        print(
            f"Created: "
            f"{created}"
        )

        print(
            f"Unchanged: "
            f"{unchanged}"
        )

        print()
        print(
            "STATUS: OK"
        )

        print("=" * 80)

    except Exception:

        db.rollback()
        raise

    finally:

        db.close()


if __name__ == "__main__":
    run()