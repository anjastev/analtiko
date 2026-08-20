from fastapi import (
    APIRouter,
    Depends,
)

from sqlalchemy.orm import Session

from app.database.database import (
    get_db,
)

from app.models.ml_prediction_snapshot import (
    MLPredictionSnapshot,
)

from app.models.match import (
    Match,
)


router = APIRouter(
    prefix="/api/ml-analytics",
    tags=["ML Analytics"],
)


# ============================================================
# HELPERS
# ============================================================

def calculate_accuracy(
    items,
):

    evaluated = [
        item
        for item in items
        if item.correct is not None
    ]


    correct = [
        item
        for item in evaluated
        if item.correct is True
    ]


    evaluated_count = (
        len(
            evaluated
        )
    )


    correct_count = (
        len(
            correct
        )
    )


    if evaluated_count > 0:

        accuracy = round(
            (
                correct_count
                / evaluated_count
            )
            * 100,
            1,
        )

    else:

        accuracy = None


    return {
        "total":
            len(
                items
            ),

        "evaluated":
            evaluated_count,

        "correct":
            correct_count,

        "accuracy":
            accuracy,
    }


# ============================================================
# PERFORMANCE
# ============================================================

@router.get("/performance")
def get_ml_performance(
    db: Session = Depends(
        get_db
    ),
):

    # ========================================================
    # ALL SNAPSHOTS
    # ========================================================

    snapshots = (
        db.query(
            MLPredictionSnapshot
        )
        .order_by(
            MLPredictionSnapshot
            .created_at
            .desc()
        )
        .all()
    )


    total_snapshots = (
        len(
            snapshots
        )
    )


    pending = [
        item
        for item in snapshots
        if item.correct is None
    ]


    evaluated = [
        item
        for item in snapshots
        if item.correct is not None
    ]


    correct_predictions = [
        item
        for item in evaluated
        if item.correct is True
    ]


    evaluated_count = (
        len(
            evaluated
        )
    )


    correct_count = (
        len(
            correct_predictions
        )
    )


    if evaluated_count > 0:

        overall_accuracy = round(
            (
                correct_count
                / evaluated_count
            )
            * 100,
            1,
        )

    else:

        overall_accuracy = None


    # ========================================================
    # STRONG PICKS
    # ========================================================

    strong_snapshots = [
        item
        for item in snapshots
        if item.is_strong_pick
    ]


    strong_metrics = (
        calculate_accuracy(
            strong_snapshots
        )
    )


    # ========================================================
    # ELITE PICKS
    # ========================================================

    elite_snapshots = [
        item
        for item in snapshots
        if item.is_elite_pick
    ]


    elite_metrics = (
        calculate_accuracy(
            elite_snapshots
        )
    )


    # ========================================================
    # CONFIDENCE LEVELS
    # ========================================================

    confidence_levels = []


    for level in [
        "ELITE",
        "STRONG",
        "MEDIUM",
        "LOW",
    ]:

        level_snapshots = [
            item
            for item in snapshots
            if item.confidence_level
            == level
        ]


        metrics = (
            calculate_accuracy(
                level_snapshots
            )
        )


        confidence_levels.append(
            {
                "level":
                    level,

                "total":
                    metrics[
                        "total"
                    ],

                "evaluated":
                    metrics[
                        "evaluated"
                    ],

                "correct":
                    metrics[
                        "correct"
                    ],

                "accuracy":
                    metrics[
                        "accuracy"
                    ],
            }
        )


    # ========================================================
    # BY LEAGUE
    # ========================================================

    league_data = {}


    for snapshot in snapshots:

        league = (
            snapshot.league
        )


        if league not in league_data:

            league_data[
                league
            ] = {
                "snapshots": 0,

                "evaluated": 0,
                "correct": 0,

                "strong_picks": 0,
                "strong_evaluated": 0,
                "strong_correct": 0,

                "elite_picks": 0,
                "elite_evaluated": 0,
                "elite_correct": 0,
            }


        values = (
            league_data[
                league
            ]
        )


        values[
            "snapshots"
        ] += 1


        # ====================================================
        # OVERALL
        # ====================================================

        if snapshot.correct is not None:

            values[
                "evaluated"
            ] += 1


            if snapshot.correct:

                values[
                    "correct"
                ] += 1


        # ====================================================
        # STRONG
        # ====================================================

        if snapshot.is_strong_pick:

            values[
                "strong_picks"
            ] += 1


            if snapshot.correct is not None:

                values[
                    "strong_evaluated"
                ] += 1


                if snapshot.correct:

                    values[
                        "strong_correct"
                    ] += 1


        # ====================================================
        # ELITE
        # ====================================================

        if snapshot.is_elite_pick:

            values[
                "elite_picks"
            ] += 1


            if snapshot.correct is not None:

                values[
                    "elite_evaluated"
                ] += 1


                if snapshot.correct:

                    values[
                        "elite_correct"
                    ] += 1


    leagues = []


    for (
        league,
        values,
    ) in league_data.items():

        # ====================================================
        # OVERALL ACCURACY
        # ====================================================

        league_accuracy = None


        if (
            values[
                "evaluated"
            ]
            > 0
        ):

            league_accuracy = round(
                (
                    values[
                        "correct"
                    ]
                    /
                    values[
                        "evaluated"
                    ]
                )
                * 100,
                1,
            )


        # ====================================================
        # STRONG ACCURACY
        # ====================================================

        strong_accuracy = None


        if (
            values[
                "strong_evaluated"
            ]
            > 0
        ):

            strong_accuracy = round(
                (
                    values[
                        "strong_correct"
                    ]
                    /
                    values[
                        "strong_evaluated"
                    ]
                )
                * 100,
                1,
            )


        # ====================================================
        # ELITE ACCURACY
        # ====================================================

        elite_accuracy = None


        if (
            values[
                "elite_evaluated"
            ]
            > 0
        ):

            elite_accuracy = round(
                (
                    values[
                        "elite_correct"
                    ]
                    /
                    values[
                        "elite_evaluated"
                    ]
                )
                * 100,
                1,
            )


        leagues.append(
            {
                "league":
                    league,

                "snapshots":
                    values[
                        "snapshots"
                    ],

                "evaluated":
                    values[
                        "evaluated"
                    ],

                "correct":
                    values[
                        "correct"
                    ],

                "accuracy":
                    league_accuracy,

                "strong_picks":
                    values[
                        "strong_picks"
                    ],

                "strong_evaluated":
                    values[
                        "strong_evaluated"
                    ],

                "strong_correct":
                    values[
                        "strong_correct"
                    ],

                "strong_accuracy":
                    strong_accuracy,

                "elite_picks":
                    values[
                        "elite_picks"
                    ],

                "elite_evaluated":
                    values[
                        "elite_evaluated"
                    ],

                "elite_correct":
                    values[
                        "elite_correct"
                    ],

                "elite_accuracy":
                    elite_accuracy,
            }
        )


    leagues.sort(
        key=lambda item:
            (
                item[
                    "evaluated"
                ],
                item[
                    "snapshots"
                ],
            ),
        reverse=True,
    )


    # ========================================================
    # RECENT RESULTS
    # ========================================================

    recent_results = []


    recent_evaluated = (
        db.query(
            MLPredictionSnapshot
        )
        .filter(
            MLPredictionSnapshot
            .correct
            .isnot(None)
        )
        .order_by(
            MLPredictionSnapshot
            .evaluated_at
            .desc()
        )
        .limit(20)
        .all()
    )


    for snapshot in recent_evaluated:

        match = (
            db.query(Match)
            .filter(
                Match.id
                == snapshot.match_id
            )
            .first()
        )


        if not match:

            continue


        recent_results.append(
            {
                "snapshot_id":
                    snapshot.id,

                "match_id":
                    snapshot.match_id,

                "league":
                    snapshot.league,

                "home_team":
                    match.home_team.name,

                "away_team":
                    match.away_team.name,

                "match_date":
                    match.match_date,

                "home_score":
                    match.home_score,

                "away_score":
                    match.away_score,

                "pick":
                    snapshot.pick,

                "actual_result":
                    snapshot.actual_result,

                "correct":
                    snapshot.correct,

                "confidence":
                    snapshot.confidence,

                "margin":
                    snapshot.margin,

                "analitiko_score":
                    snapshot.analitiko_score,

                "league_threshold":
                    snapshot.league_threshold,

                "elite_threshold":
                    snapshot.elite_threshold,

                "is_strong_pick":
                    snapshot.is_strong_pick,

                "is_elite_pick":
                    snapshot.is_elite_pick,

                "confidence_level":
                    snapshot.confidence_level,

                "model_version":
                    snapshot.model_version,

                "created_at":
                    snapshot.created_at,

                "evaluated_at":
                    snapshot.evaluated_at,
            }
        )


    # ========================================================
    # RECENT PENDING
    # ========================================================

    recent_pending = []


    pending_snapshots = (
        db.query(
            MLPredictionSnapshot
        )
        .filter(
            MLPredictionSnapshot
            .correct
            .is_(None)
        )
        .order_by(
            MLPredictionSnapshot
            .created_at
            .desc()
        )
        .limit(20)
        .all()
    )


    for snapshot in pending_snapshots:

        match = (
            db.query(Match)
            .filter(
                Match.id
                == snapshot.match_id
            )
            .first()
        )


        if not match:

            continue


        recent_pending.append(
            {
                "snapshot_id":
                    snapshot.id,

                "match_id":
                    snapshot.match_id,

                "league":
                    snapshot.league,

                "home_team":
                    match.home_team.name,

                "away_team":
                    match.away_team.name,

                "match_date":
                    match.match_date,

                "status":
                    match.status,

                "pick":
                    snapshot.pick,

                "confidence":
                    snapshot.confidence,

                "margin":
                    snapshot.margin,

                "analitiko_score":
                    snapshot.analitiko_score,

                "league_threshold":
                    snapshot.league_threshold,

                "elite_threshold":
                    snapshot.elite_threshold,

                "is_strong_pick":
                    snapshot.is_strong_pick,

                "is_elite_pick":
                    snapshot.is_elite_pick,

                "confidence_level":
                    snapshot.confidence_level,

                "model_version":
                    snapshot.model_version,

                "created_at":
                    snapshot.created_at,
            }
        )


    # ========================================================
    # RETURN
    # ========================================================

    return {
        "model":
            "logistic_regression_v2",

        "experimental":
            True,

        "validation": {
            "strict_oos_matches":
                283,

            "strict_oos_accuracy":
                49.1,

            "strict_oos_strong_accuracy":
                58.1,

            "strict_oos_strong_coverage":
                15.2,

            "strict_oos_elite_accuracy":
                69.7,

            "elite_threshold":
                50.0,

            "note": (
                "Strict OOS metrics are frozen "
                "research results from the untouched "
                "historical holdout and are separate "
                "from live performance."
            ),
        },

        "summary": {
            "total_snapshots":
                total_snapshots,

            "pending":
                len(
                    pending
                ),

            "evaluated":
                evaluated_count,

            "correct":
                correct_count,

            "accuracy":
                overall_accuracy,
        },

        "strong_picks": {
            "total":
                strong_metrics[
                    "total"
                ],

            "evaluated":
                strong_metrics[
                    "evaluated"
                ],

            "correct":
                strong_metrics[
                    "correct"
                ],

            "accuracy":
                strong_metrics[
                    "accuracy"
                ],
        },

        "elite_picks": {
            "threshold":
                50.0,

            "total":
                elite_metrics[
                    "total"
                ],

            "evaluated":
                elite_metrics[
                    "evaluated"
                ],

            "correct":
                elite_metrics[
                    "correct"
                ],

            "accuracy":
                elite_metrics[
                    "accuracy"
                ],
        },

        "confidence_levels":
            confidence_levels,

        "by_league":
            leagues,

        "recent_results":
            recent_results,

        "recent_pending":
            recent_pending,

        "note": (
            "Live ML performance uses only saved "
            "pre-match prediction snapshots. "
            "Historical strict OOS metrics are "
            "reported separately and are never "
            "mixed into live accuracy."
        ),
    }