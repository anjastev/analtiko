from datetime import (
    datetime,
    timezone,
)

from sqlalchemy import and_

from app.database.database import (
    Base,
    SessionLocal,
    engine,
)

from app.models.market import Market
from app.models.market_prediction import (
    MarketPrediction,
)
from app.models.match import Match
from app.models.signal import Signal

from app.services.signal_engine import (
    evaluate_prediction_signal,
)

import app.models


# ============================================================
# CONFIG
# ============================================================

SPORT = "football"

MARKET_CODE = "DC"

MODEL_VERSION = (
    "logistic_regression_v2_derived_markets"
)


# ============================================================
# HELPERS
# ============================================================

def get_double_chance_market(
    db,
):
    return (
        db.query(Market)
        .filter(
            Market.sport
            == SPORT,

            Market.code
            == MARKET_CODE,
        )
        .first()
    )


def signal_exists(
    db,
    prediction: MarketPrediction,
) -> bool:

    existing = (
        db.query(Signal)
        .filter(
            and_(
                Signal.match_id
                == prediction.match_id,

                Signal.market_id
                == prediction.market_id,

                Signal.prediction_id
                == prediction.id,

                Signal.selection
                == prediction.selection,

                Signal.active
                .is_(True),
            )
        )
        .first()
    )

    return (
        existing is not None
    )


# ============================================================
# MAIN
# ============================================================

def run():

    Base.metadata.create_all(
        bind=engine
    )

    db = SessionLocal()

    now = datetime.now(
        timezone.utc
    )

    total_predictions = 0
    qualified = 0
    created = 0
    unchanged = 0
    skipped_low_probability = 0

    try:

        # ====================================================
        # MARKET
        # ====================================================

        market = (
            get_double_chance_market(
                db
            )
        )

        if market is None:

            raise RuntimeError(
                "Double Chance market missing. "
                "Run scripts.add_football_markets first."
            )

        # ====================================================
        # UPCOMING DOUBLE CHANCE PREDICTIONS
        # ====================================================

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

                MarketPrediction.model_version
                == MODEL_VERSION,

                Match.match_date
                >= now,

                MarketPrediction.actual_result
                .is_(None),
            )
            .order_by(
                Match.match_date.asc(),
                MarketPrediction.probability.desc(),
            )
            .all()
        )

        print()
        print("=" * 80)
        print(
            "ANALITIKO SIGNAL ENGINE"
        )
        print("=" * 80)

        print(
            f"Sport: "
            f"{SPORT}"
        )

        print(
            f"Market: "
            f"{MARKET_CODE}"
        )

        print(
            f"Model: "
            f"{MODEL_VERSION}"
        )

        print(
            f"Predictions found: "
            f"{len(predictions)}"
        )

        # ====================================================
        # PROCESS
        # ====================================================

        for prediction in predictions:

            total_predictions += 1

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

            decision = (
                evaluate_prediction_signal(
                    prediction.probability
                )
            )

            print()
            print("-" * 80)

            print(
                f"[{match.id}] "
                f"{match.home_team.name} "
                f"vs "
                f"{match.away_team.name}"
            )

            print(
                f"Selection: "
                f"{prediction.selection}"
            )

            print(
                f"Probability: "
                f"{prediction.probability:.1f}%"
            )

            if not decision.qualifies:

                skipped_low_probability += 1

                print(
                    "Signal: NONE"
                )

                continue

            qualified += 1

            print(
                f"Signal: "
                f"{decision.signal_type}"
            )

            print(
                f"Risk: "
                f"{decision.risk_level}"
            )

            if signal_exists(
                db=db,
                prediction=prediction,
            ):

                unchanged += 1

                print(
                    "UNCHANGED"
                )

                continue

            signal = Signal(
                match_id=prediction.match_id,
                market_id=prediction.market_id,
                prediction_id=prediction.id,

                signal_type=(
                    decision.signal_type
                ),

                selection=(
                    prediction.selection
                ),

                model_probability=(
                    prediction.probability
                ),

                market_probability=None,

                edge=None,

                odds=None,

                confidence_score=(
                    decision.confidence_score
                ),

                risk_level=(
                    decision.risk_level
                ),

                active=True,
            )

            db.add(
                signal
            )

            created += 1

            print(
                "SAVED"
            )

        # ====================================================
        # COMMIT
        # ====================================================

        db.commit()

        # ====================================================
        # SUMMARY
        # ====================================================

        print()
        print("=" * 80)
        print(
            "SIGNAL ENGINE SUMMARY"
        )
        print("=" * 80)

        print(
            f"Predictions processed:    "
            f"{total_predictions}"
        )

        print(
            f"Qualified signals:        "
            f"{qualified}"
        )

        print(
            f"Signals created:          "
            f"{created}"
        )

        print(
            f"Signals unchanged:        "
            f"{unchanged}"
        )

        print(
            f"Below threshold:          "
            f"{skipped_low_probability}"
        )

        print()

        if total_predictions == 0:

            print(
                "STATUS: PARTIAL "
                "(no qualifying market predictions available)"
            )

        else:

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