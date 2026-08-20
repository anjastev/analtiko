from fastapi import APIRouter, HTTPException

from scripts.sync_selected_fixtures import run as sync_fixtures
from scripts.sync_odds import run as sync_odds
from scripts.sync_results import run as sync_results
from scripts.sync_history import run as sync_history
from scripts.snapshot_predictions import run as snapshot_predictions
from scripts.evaluate_predictions import run as evaluate_predictions


router = APIRouter(
    prefix="/api/admin",
    tags=["Admin"],
)


def execute_job(
    name: str,
    function,
):
    try:
        function()

        return {
            "success": True,
            "job": name,
            "message": f"{name} completed successfully.",
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail={
                "job": name,
                "error": str(error),
            },
        )


@router.post("/sync-fixtures")
def run_sync_fixtures():
    return execute_job(
        "Fixtures sync",
        sync_fixtures,
    )


@router.post("/sync-odds")
def run_sync_odds():
    return execute_job(
        "Odds sync",
        sync_odds,
    )


@router.post("/sync-results")
def run_sync_results():
    return execute_job(
        "Results sync",
        sync_results,
    )


@router.post("/sync-history")
def run_sync_history():
    return execute_job(
        "History sync",
        sync_history,
    )


@router.post("/snapshot-predictions")
def run_snapshot_predictions():
    return execute_job(
        "Prediction snapshot",
        snapshot_predictions,
    )


@router.post("/evaluate-predictions")
def run_evaluate_predictions():
    return execute_job(
        "Prediction evaluation",
        evaluate_predictions,
    )