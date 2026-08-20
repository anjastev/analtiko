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

from app.models.match import Match
from app.models.market import Market
from app.models.market_prediction import (
    MarketPrediction,
)
from app.models.ml_prediction_snapshot import (
    MLPredictionSnapshot,
)

import app.models


# ============================================================
# CONFIG
# ============================================================

SOURCE_MODEL_VERSION = (
    "logistic_regression_v2"
)

DERIVED_MODEL_VERSION = (
    "logistic_regression_v2_derived_markets"
)

# Minimum probability for derived selections to be marked
# as recommended.
#
# This is NOT a validated betting threshold yet.
# It is only a temporary product/research rule.
RECOMMENDED_PROBABILITY = 70.0


# ============================================================
# HELPERS
# ============================================================

def normalize_probability(
    value: float,
) -> float:
    """
    Existing ML snapshots store probabilities as percentages.

    Example:
        58.3

    Keep the same convention in market_predictions.
    """

    return round(
        float(value),
        4,
    )


def probability_level(
    probability: float,
) -> str:
    """
    Generic derived confidence band.

    This is separate from the frozen v2 Analitiko Score tiers.
    """

    if probability >= 80.0:
        return "ULTRA"

    if probability >= 70.0:
        return "ELITE"

    if probability >= 60.0:
        return "STRONG"

    if probability >= 50.0:
        return "MEDIUM"

    return "LOW"


def get_market(
    db,
    code: str,
):
    return (
        db.query(Market)
        .filter(
            Market.sport
            == "football",
            Market.code
            == code,
        )
        .first()
    )


def get_latest_ml_snapshot(
    db,
    match_id: int,
):
    return (
        db.query(
            MLPredictionSnapshot
        )
        .filter(
            MLPredictionSnapshot.match_id
            == match_id,
            MLPredictionSnapshot.model_version
            == SOURCE_MODEL_VERSION,
        )
        .order_by(
            MLPredictionSnapshot.created_at.desc(),
            MLPredictionSnapshot.id.desc(),
        )
        .first()
    )


def prediction_exists(
    db,
    match_id: int,
    market_id: int,
    model_version: str,
    selection: str,
) -> bool:

    existing = (
        db.query(
            MarketPrediction
        )
        .filter(
            and_(
                MarketPrediction.match_id
                == match_id,

                MarketPrediction.market_id
                == market_id,

                MarketPrediction.model_version
                == model_version,

                MarketPrediction.selection
                == selection,

                MarketPrediction.actual_result
                .is_(None),
            )
        )
        .first()
    )

    return (
        existing
        is not None
    )


def save_prediction(
    db,
    match_id: int,
    market: Market,
    selection: str,
    probability: float,
    model_version: str,
):
    """
    Save a derived market prediction if it does not already
    exist as a pending prediction for the same match/market/
    model/selection.
    """

    probability = (
        normalize_probability(
            probability
        )
    )

    if prediction_exists(
        db=db,
        match_id=match_id,
        market_id=market.id,
        model_version=model_version,
        selection=selection,
    ):

        return False

    level = (
        probability_level(
            probability
        )
    )

    row = MarketPrediction(
        match_id=match_id,
        market_id=market.id,
        model_version=model_version,
        selection=selection,
        probability=probability,

        # For derived markets, confidence is currently the
        # probability itself.
        confidence=probability,

        confidence_level=level,

        is_recommended=(
            probability
            >= RECOMMENDED_PROBABILITY
        ),

        created_at=datetime.now(
            timezone.utc
        ),
    )

    db.add(
        row
    )

    return True


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

    total_matches = 0
    with_ml = 0
    skipped_no_ml = 0
    created = 0
    unchanged = 0

    try:

        # ====================================================
        # REQUIRED MARKETS
        # ====================================================

        market_1x2 = (
            get_market(
                db,
                "1X2",
            )
        )

        market_dc = (
            get_market(
                db,
                "DC",
            )
        )

        if (
            market_1x2
            is None
            or market_dc
            is None
        ):

            raise RuntimeError(
                "Required football markets are missing. "
                "Run scripts.add_football_markets first."
            )

        # ====================================================
        # UPCOMING MATCHES
        # ====================================================

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
        print("=" * 80)
        print(
            "ANALITIKO MARKET PREDICTION SNAPSHOT"
        )
        print("=" * 80)

        print(
            f"Upcoming matches: "
            f"{len(matches)}"
        )

        print(
            f"Source model: "
            f"{SOURCE_MODEL_VERSION}"
        )

        print(
            f"Derived model: "
            f"{DERIVED_MODEL_VERSION}"
        )

        print(
            f"Recommended probability: "
            f"{RECOMMENDED_PROBABILITY:.1f}%"
        )

        # ====================================================
        # PROCESS MATCHES
        # ====================================================

        for match in matches:

            total_matches += 1

            ml = (
                get_latest_ml_snapshot(
                    db=db,
                    match_id=match.id,
                )
            )

            if ml is None:

                skipped_no_ml += 1

                continue

            with_ml += 1

            home_probability = (
                normalize_probability(
                    ml.home_probability
                )
            )

            draw_probability = (
                normalize_probability(
                    ml.draw_probability
                )
            )

            away_probability = (
                normalize_probability(
                    ml.away_probability
                )
            )

            # =================================================
            # DERIVED DOUBLE CHANCE
            # =================================================

            probability_1x = (
                home_probability
                + draw_probability
            )

            probability_x2 = (
                draw_probability
                + away_probability
            )

            probability_12 = (
                home_probability
                + away_probability
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
                f"Kickoff: "
                f"{match.match_date}"
            )

            print(
                f"ML: "
                f"H={home_probability:.1f}% "
                f"D={draw_probability:.1f}% "
                f"A={away_probability:.1f}%"
            )

            print(
                f"DC: "
                f"1X={probability_1x:.1f}% "
                f"X2={probability_x2:.1f}% "
                f"12={probability_12:.1f}%"
            )

            # =================================================
            # 1X2
            # =================================================

            rows = [
                (
                    market_1x2,
                    "HOME",
                    home_probability,
                    SOURCE_MODEL_VERSION,
                ),
                (
                    market_1x2,
                    "DRAW",
                    draw_probability,
                    SOURCE_MODEL_VERSION,
                ),
                (
                    market_1x2,
                    "AWAY",
                    away_probability,
                    SOURCE_MODEL_VERSION,
                ),

                # =============================================
                # DOUBLE CHANCE
                # =============================================

                (
                    market_dc,
                    "1X",
                    probability_1x,
                    DERIVED_MODEL_VERSION,
                ),
                (
                    market_dc,
                    "X2",
                    probability_x2,
                    DERIVED_MODEL_VERSION,
                ),
                (
                    market_dc,
                    "12",
                    probability_12,
                    DERIVED_MODEL_VERSION,
                ),
            ]

            created_for_match = 0

            for (
                market,
                selection,
                probability,
                model_version,
            ) in rows:

                was_created = (
                    save_prediction(
                        db=db,
                        match_id=match.id,
                        market=market,
                        selection=selection,
                        probability=probability,
                        model_version=model_version,
                    )
                )

                if was_created:

                    created += 1
                    created_for_match += 1

                else:

                    unchanged += 1

            if created_for_match:

                print(
                    f"Saved: "
                    f"{created_for_match}"
                )

            else:

                print(
                    "UNCHANGED"
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
            "MARKET PREDICTION SUMMARY"
        )
        print("=" * 80)

        print(
            f"Upcoming matches:        "
            f"{total_matches}"
        )

        print(
            f"Matches with ML:         "
            f"{with_ml}"
        )

        print(
            f"Matches without ML:      "
            f"{skipped_no_ml}"
        )

        print(
            f"Predictions created:     "
            f"{created}"
        )

        print(
            f"Predictions unchanged:   "
            f"{unchanged}"
        )

        print()

        if with_ml == 0:

            print(
                "STATUS: PARTIAL "
                "(no upcoming ML snapshots)"
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