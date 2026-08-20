from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db

from app.models.prediction_snapshot import PredictionSnapshot

from sqlalchemy import func

from app.models.match import Match
from app.models.odds import Odds
from app.models.team_match_history import TeamMatchHistory


router = APIRouter(
    prefix="/api/analytics",
    tags=["Analytics"],
)


@router.get("/model-performance")
def get_model_performance(
    db: Session = Depends(get_db),
):
    evaluated = (
        db.query(PredictionSnapshot)
        .filter(
            PredictionSnapshot.result_correct.isnot(None)
        )
        .all()
    )

    total = len(evaluated)

    if total == 0:
        return {
            "evaluated_predictions": 0,

            "result_accuracy": None,

            "high_confidence": {
                "predictions": 0,
                "accuracy": None,
            },

            "over_25": {
                "predictions": 0,
                "accuracy": None,
            },

            "btts": {
                "predictions": 0,
                "accuracy": None,
            },
        }

    # ==========================================
    # RESULT ACCURACY
    # ==========================================

    correct_results = sum(
        1
        for item in evaluated
        if item.result_correct == 1
    )

    result_accuracy = (
        correct_results
        / total
    ) * 100

    # ==========================================
    # HIGH CONFIDENCE
    # ==========================================

    high_confidence = [
        item
        for item in evaluated
        if item.confidence >= 70
    ]

    high_confidence_correct = sum(
        1
        for item in high_confidence
        if item.result_correct == 1
    )

    high_confidence_accuracy = (
        (
            high_confidence_correct
            / len(high_confidence)
        ) * 100
        if high_confidence
        else None
    )

    # ==========================================
    # OVER 2.5
    # ==========================================

    over_predictions = [
        item
        for item in evaluated
        if item.over_25_correct is not None
    ]

    over_correct = sum(
        1
        for item in over_predictions
        if item.over_25_correct == 1
    )

    over_accuracy = (
        (
            over_correct
            / len(over_predictions)
        ) * 100
        if over_predictions
        else None
    )

    # ==========================================
    # BTTS
    # ==========================================

    btts_predictions = [
        item
        for item in evaluated
        if item.btts_correct is not None
    ]

    btts_correct = sum(
        1
        for item in btts_predictions
        if item.btts_correct == 1
    )

    btts_accuracy = (
        (
            btts_correct
            / len(btts_predictions)
        ) * 100
        if btts_predictions
        else None
    )

    return {
        "evaluated_predictions":
            total,

        "result_accuracy":
            round(
                result_accuracy,
                1,
            ),

        "high_confidence": {
            "predictions":
                len(high_confidence),

            "accuracy":
                (
                    round(
                        high_confidence_accuracy,
                        1,
                    )
                    if high_confidence_accuracy
                    is not None
                    else None
                ),
        },

        "over_25": {
            "predictions":
                len(over_predictions),

            "accuracy":
                (
                    round(
                        over_accuracy,
                        1,
                    )
                    if over_accuracy
                    is not None
                    else None
                ),
        },

        "btts": {
            "predictions":
                len(btts_predictions),

            "accuracy":
                (
                    round(
                        btts_accuracy,
                        1,
                    )
                    if btts_accuracy
                    is not None
                    else None
                ),
        },
    }


@router.get("/system-status")
def get_system_status(
    db: Session = Depends(get_db),
):
    latest_match = (
        db.query(
            func.max(Match.updated_at)
        )
        .scalar()
        if hasattr(Match, "updated_at")
        else None
    )

    latest_odds = (
        db.query(
            func.max(Odds.recorded_at)
        )
        .scalar()
    )

    latest_history = (
        db.query(
            func.max(
                TeamMatchHistory.match_date
            )
        )
        .scalar()
    )

    latest_snapshot = (
        db.query(
            func.max(
                PredictionSnapshot.created_at
            )
        )
        .scalar()
    )

    latest_official = (
        db.query(
            func.max(
                PredictionSnapshot.official_at
            )
        )
        .filter(
            PredictionSnapshot.is_official == 1
        )
        .scalar()
    )

    finished_matches = (
        db.query(Match)
        .filter(
            Match.status.in_(
                ["FT", "AET", "PEN"]
            )
        )
        .count()
    )

    matches_with_odds = (
        db.query(
            Odds.match_id
        )
        .distinct()
        .count()
    )

    teams_with_history = (
        db.query(
            TeamMatchHistory.team_id
        )
        .distinct()
        .count()
    )

    snapshots_count = (
        db.query(
            PredictionSnapshot
        )
        .count()
    )

    official_count = (
        db.query(
            PredictionSnapshot
        )
        .filter(
            PredictionSnapshot.is_official == 1
        )
        .count()
    )

    return {
        "freshness": {
            "fixtures": latest_match,
            "odds": latest_odds,
            "history": latest_history,
            "predictions": latest_snapshot,
            "official_predictions": latest_official,
        },

        "coverage": {
            "total_matches":
                db.query(Match).count(),

            "finished_matches":
                finished_matches,

            "matches_with_odds":
                matches_with_odds,

            "teams_with_history":
                teams_with_history,

            "prediction_snapshots":
                snapshots_count,

            "official_predictions":
                official_count,
        },
    }