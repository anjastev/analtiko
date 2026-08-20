from fastapi import (
    APIRouter,
    Depends,
)

from sqlalchemy.orm import Session

from app.database.database import (
    get_db,
)

from app.models.match import Match

from app.models.value_prediction_snapshot import (
    ValuePredictionSnapshot,
)


router = APIRouter(
    prefix="/api/value-analytics",
    tags=[
        "Value Analytics",
    ],
)


def calculate_group(
    snapshots,
):

    total = len(
        snapshots
    )


    evaluated_items = [
        item
        for item
        in snapshots
        if item.correct is not None
    ]


    evaluated = len(
        evaluated_items
    )


    correct = sum(
        1
        for item
        in evaluated_items
        if item.correct
    )


    profit = sum(
        float(
            item.profit
            or 0.0
        )
        for item
        in evaluated_items
    )


    accuracy = (
        correct
        / evaluated
        * 100
        if evaluated > 0
        else None
    )


    roi = (
        profit
        / evaluated
        * 100
        if evaluated > 0
        else None
    )


    avg_edge = (
        sum(
            float(
                item.edge
            )
            for item
            in snapshots
        )
        / total
        if total > 0
        else None
    )


    avg_odds = (
        sum(
            float(
                item.market_odds
            )
            for item
            in snapshots
        )
        / total
        if total > 0
        else None
    )


    return {
        "total":
            total,

        "pending":
            total
            - evaluated,

        "evaluated":
            evaluated,

        "correct":
            correct,

        "accuracy":
            round(
                accuracy,
                1,
            )
            if accuracy is not None
            else None,

        "profit":
            round(
                profit,
                2,
            ),

        "roi":
            round(
                roi,
                1,
            )
            if roi is not None
            else None,

        "average_edge":
            round(
                avg_edge,
                1,
            )
            if avg_edge is not None
            else None,

        "average_odds":
            round(
                avg_odds,
                2,
            )
            if avg_odds is not None
            else None,
    }


@router.get(
    "/performance"
)
def get_value_performance(
    db: Session = Depends(
        get_db
    ),
):

    snapshots = (
        db.query(
            ValuePredictionSnapshot
        )
        .order_by(
            ValuePredictionSnapshot
            .created_at
            .desc()
        )
        .all()
    )


    value_items = [
        item
        for item
        in snapshots
        if item.is_value_pick
    ]


    elite_items = [
        item
        for item
        in snapshots
        if item.is_elite_value
    ]


    consensus_items = [
        item
        for item
        in snapshots
        if item.same_as_model_pick
    ]


    recent = []


    for snapshot in snapshots[
        :20
    ]:

        match = (
            db.query(
                Match
            )
            .filter(
                Match.id
                == snapshot.match_id
            )
            .first()
        )


        if match is None:

            continue


        recent.append(
            {
                "id":
                    snapshot.id,

                "match_id":
                    snapshot.match_id,

                "league":
                    match.league.name,

                "home_team":
                    match.home_team.name,

                "away_team":
                    match.away_team.name,

                "match_date":
                    match.match_date,

                "value_pick":
                    snapshot.value_pick,

                "model_pick":
                    snapshot.model_pick,

                "model_probability":
                    snapshot.model_probability,

                "market_probability":
                    snapshot.market_probability,

                "edge":
                    snapshot.edge,

                "market_odds":
                    snapshot.market_odds,

                "fair_odds":
                    snapshot.fair_odds,

                "expected_value":
                    snapshot.expected_value,

                "analitiko_score":
                    snapshot.analitiko_score,

                "is_strong_pick":
                    snapshot.is_strong_pick,

                "is_elite_pick":
                    snapshot.is_elite_pick,

                "is_elite_value":
                    snapshot.is_elite_value,

                "same_as_model_pick":
                    snapshot.same_as_model_pick,

                "bookmaker":
                    snapshot.bookmaker,

                "created_at":
                    snapshot.created_at,

                "actual_result":
                    snapshot.actual_result,

                "correct":
                    snapshot.correct,

                "profit":
                    snapshot.profit,

                "roi":
                    snapshot.roi,
            }
        )


    return {
        "model":
            "logistic_regression_v2",

        "status":
            "prospective_research",

        "thresholds": {
            "value_edge":
                5.0,

            "elite_value_edge":
                8.0,
        },

        "summary":
            calculate_group(
                snapshots
            ),

        "value":
            calculate_group(
                value_items
            ),

        "elite_value":
            calculate_group(
                elite_items
            ),

        "model_consensus":
            calculate_group(
                consensus_items
            ),

        "recent":
            recent,

        "note":
            (
                "VALUE and ELITE VALUE are "
                "prospective research signals. "
                "The 5% and 8% edge thresholds "
                "are not historically validated "
                "and must not be retuned from "
                "small live samples."
            ),
    }