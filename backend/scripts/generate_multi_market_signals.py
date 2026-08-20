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
from app.models.signal import Signal

from app.services.market_policy import (
    MARKET_POLICIES,
    get_market_policy,
)

from app.services.match_data_quality import (
    is_match_production_ready,
)


def get_signal_type(
    probability: float,
):

    if probability >= 85.0:
        return (
            "ULTRA",
            "LOW",
        )

    if probability >= 80.0:
        return (
            "ELITE",
            "LOW_MEDIUM",
        )

    return (
        "STRONG",
        "MEDIUM",
    )


def get_active_signal(
    db,
    prediction_id: int,
):

    return (
        db.query(Signal)
        .filter(
            Signal.prediction_id
            == prediction_id,

            Signal.active
            .is_(True),
        )
        .first()
    )


def run():

    db = SessionLocal()

    now = datetime.now(
        timezone.utc
    )

    created = 0
    unchanged = 0
    below_threshold = 0

    research_blocked = 0
    disabled_blocked = 0
    data_blocked = 0

    stale_signals_deactivated = 0

    try:

        market_codes = list(
            MARKET_POLICIES.keys()
        )

        markets = (
            db.query(Market)
            .filter(
                Market.sport
                == "football",

                Market.code.in_(
                    market_codes
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

        match_cache = {}
        quality_cache = {}

        print()
        print("=" * 100)
        print(
            "ANALITIKO PRODUCTION SIGNAL ENGINE"
        )
        print("=" * 100)

        print(
            f"Predictions found: "
            f"{len(predictions)}"
        )

        for prediction in predictions:

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

            # =================================================
            # MARKET POLICY
            # =================================================

            if not policy.allow_signals:

                if (
                    policy.status
                    == "RESEARCH"
                ):
                    research_blocked += 1

                else:
                    disabled_blocked += 1

                continue

            # =================================================
            # MATCH
            # =================================================

            match = (
                match_cache.get(
                    prediction.match_id
                )
            )

            if match is None:

                match = (
                    db.query(Match)
                    .filter(
                        Match.id
                        == prediction.match_id
                    )
                    .first()
                )

                match_cache[
                    prediction.match_id
                ] = match

            if match is None:
                continue

            # =================================================
            # PRODUCTION DATA GATE
            # =================================================

            if (
                prediction.match_id
                not in quality_cache
            ):

                quality_cache[
                    prediction.match_id
                ] = (
                    is_match_production_ready(
                        db=db,
                        match=match,
                    )
                )

            production_ready = (
                quality_cache[
                    prediction.match_id
                ]
            )

            existing_signal = (
                get_active_signal(
                    db=db,
                    prediction_id=(
                        prediction.id
                    ),
                )
            )

            if not production_ready:

                data_blocked += 1

                if existing_signal:

                    existing_signal.active = (
                        False
                    )

                    stale_signals_deactivated += 1

                continue

            # =================================================
            # PROBABILITY GATE
            # =================================================

            probability = float(
                prediction.probability
            )

            threshold = (
                policy.min_signal_probability
            )

            if (
                threshold is None
                or
                probability
                < threshold
            ):

                below_threshold += 1

                continue

            # =================================================
            # DEDUPE
            # =================================================

            if existing_signal:

                unchanged += 1
                continue

            signal_type, risk_level = (
                get_signal_type(
                    probability
                )
            )

            signal = Signal(
                match_id=(
                    prediction.match_id
                ),

                market_id=(
                    prediction.market_id
                ),

                prediction_id=(
                    prediction.id
                ),

                signal_type=(
                    signal_type
                ),

                selection=(
                    prediction.selection
                ),

                model_probability=(
                    probability
                ),

                market_probability=None,

                edge=None,

                odds=None,

                confidence_score=(
                    probability
                ),

                risk_level=(
                    risk_level
                ),

                active=True,
            )

            db.add(
                signal
            )

            created += 1

            print(
                f"[SIGNAL] "
                f"{match.home_team.name} "
                f"vs "
                f"{match.away_team.name} | "
                f"{market.code} "
                f"{prediction.selection} "
                f"{probability:.1f}% "
                f"{signal_type}"
            )

        db.commit()

        print()
        print("=" * 100)
        print(
            "PRODUCTION SIGNAL SUMMARY"
        )
        print("=" * 100)

        print(
            f"Created:                    "
            f"{created}"
        )

        print(
            f"Unchanged:                  "
            f"{unchanged}"
        )

        print(
            f"Below probability:          "
            f"{below_threshold}"
        )

        print(
            f"Research market blocked:    "
            f"{research_blocked}"
        )

        print(
            f"Disabled market blocked:    "
            f"{disabled_blocked}"
        )

        print(
            f"Data-quality blocked:       "
            f"{data_blocked}"
        )

        print(
            f"Stale signals deactivated:  "
            f"{stale_signals_deactivated}"
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