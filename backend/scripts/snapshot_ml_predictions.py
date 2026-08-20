from datetime import (
    datetime,
    timedelta,
    timezone,
)

from app.database.database import (
    SessionLocal,
)

from app.models.match import Match

from app.models.match_stats import (
    MatchStats,
)

from app.models.team_match_history import (
    TeamMatchHistory,
)

from app.models.h2h import (
    H2HMatch,
)

from app.models.ml_prediction_snapshot import (
    MLPredictionSnapshot,
)

from app.analytics.team_form import (
    calculate_form_from_history,
)

from app.analytics.h2h import (
    calculate_h2h_scores,
)

from app.ml.ml_predictor import (
    predict_result,
)


# ============================================================
# CONFIG
# ============================================================

UPCOMING_WINDOW_DAYS = 3

MODEL_VERSION = (
    "logistic_regression_v2"
)

FINISHED_STATUSES = {
    "FT",
    "AET",
    "PEN",
}


# ============================================================
# MAIN
# ============================================================

def run():

    db = SessionLocal()

    now = datetime.now(
        timezone.utc
    )

    end = (
        now
        + timedelta(
            days=UPCOMING_WINDOW_DAYS
        )
    )


    saved = 0
    unchanged = 0
    skipped = 0
    failed = 0

    strong_count = 0
    elite_count = 0


    try:

        # ====================================================
        # UPCOMING MATCHES
        # ====================================================

        matches = (
            db.query(Match)
            .filter(
                Match.match_date
                >= now,

                Match.match_date
                <= end,

                ~Match.status.in_(
                    FINISHED_STATUSES
                ),
            )
            .order_by(
                Match.match_date.asc()
            )
            .all()
        )


        print()
        print("=" * 70)
        print(
            "ANALITIKO ML PREDICTION SNAPSHOT"
        )
        print("=" * 70)

        print(
            f"Matches to check: "
            f"{len(matches)}"
        )


        # ====================================================
        # PROCESS MATCHES
        # ====================================================

        for match in matches:

            print()
            print("-" * 70)

            print(
                f"{match.home_team.name} "
                f"vs "
                f"{match.away_team.name}"
            )

            print(
                f"League: "
                f"{match.league.name}"
            )

            print(
                f"Match ID: "
                f"{match.id}"
            )


            try:

                # =================================================
                # HISTORY
                # =================================================

                home_history = (
                    db.query(
                        TeamMatchHistory
                    )
                    .filter(
                        TeamMatchHistory.team_id
                        == match.home_team_id,

                        TeamMatchHistory.match_date
                        < match.match_date,
                    )
                    .order_by(
                        TeamMatchHistory
                        .match_date
                        .desc()
                    )
                    .limit(5)
                    .all()
                )


                away_history = (
                    db.query(
                        TeamMatchHistory
                    )
                    .filter(
                        TeamMatchHistory.team_id
                        == match.away_team_id,

                        TeamMatchHistory.match_date
                        < match.match_date,
                    )
                    .order_by(
                        TeamMatchHistory
                        .match_date
                        .desc()
                    )
                    .limit(5)
                    .all()
                )


                if (
                    not home_history
                    or
                    not away_history
                ):

                    skipped += 1

                    print(
                        "Skipped: no_history"
                    )

                    continue


                # =================================================
                # FORM
                # =================================================

                home_form = (
                    calculate_form_from_history(
                        home_history
                    )
                )


                away_form = (
                    calculate_form_from_history(
                        away_history
                    )
                )


                # =================================================
                # XG
                # =================================================

                stats = (
                    db.query(
                        MatchStats
                    )
                    .filter(
                        MatchStats.match_id
                        == match.id
                    )
                    .first()
                )


                home_xg = 1.2
                away_xg = 1.2


                if stats:

                    if (
                        stats.home_xg_avg
                        is not None
                        and
                        stats.home_xg_avg > 0
                    ):

                        home_xg = float(
                            stats.home_xg_avg
                        )


                    if (
                        stats.away_xg_avg
                        is not None
                        and
                        stats.away_xg_avg > 0
                    ):

                        away_xg = float(
                            stats.away_xg_avg
                        )


                # =================================================
                # H2H
                # =================================================

                home_external_id = (
                    match.home_team.external_id
                )


                away_external_id = (
                    match.away_team.external_id
                )


                h2h_home_score = 5.0
                h2h_away_score = 5.0
                h2h_matches_count = 0


                if (
                    home_external_id
                    and
                    away_external_id
                ):

                    h2h_matches = (
                        db.query(
                            H2HMatch
                        )
                        .filter(
                            H2HMatch.match_date
                            < match.match_date,

                            (
                                (
                                    H2HMatch
                                    .home_team_external_id
                                    == home_external_id
                                )
                                &
                                (
                                    H2HMatch
                                    .away_team_external_id
                                    == away_external_id
                                )
                            )
                            |
                            (
                                (
                                    H2HMatch
                                    .home_team_external_id
                                    == away_external_id
                                )
                                &
                                (
                                    H2HMatch
                                    .away_team_external_id
                                    == home_external_id
                                )
                            )
                        )
                        .order_by(
                            H2HMatch
                            .match_date
                            .desc()
                        )
                        .limit(5)
                        .all()
                    )


                    h2h_matches_count = (
                        len(
                            h2h_matches
                        )
                    )


                    if h2h_matches:

                        scores = (
                            calculate_h2h_scores(
                                matches=
                                    h2h_matches,

                                home_team_external_id=
                                    home_external_id,
                            )
                        )


                        h2h_home_score = float(
                            scores[
                                "home_score"
                            ]
                        )


                        h2h_away_score = float(
                            scores[
                                "away_score"
                            ]
                        )


                # =================================================
                # ML PREDICTION
                # =================================================

                prediction = (
                    predict_result(
                        league=
                            match.league.name,

                        home_form=
                            home_form[
                                "form_score"
                            ],

                        away_form=
                            away_form[
                                "form_score"
                            ],

                        home_goals_avg=
                            home_form[
                                "goals_for_avg"
                            ],

                        away_goals_avg=
                            away_form[
                                "goals_for_avg"
                            ],

                        home_goals_against_avg=
                            home_form[
                                "goals_against_avg"
                            ],

                        away_goals_against_avg=
                            away_form[
                                "goals_against_avg"
                            ],

                        home_xg=
                            home_xg,

                        away_xg=
                            away_xg,

                        h2h_home_score=
                            h2h_home_score,

                        h2h_away_score=
                            h2h_away_score,

                        h2h_matches=
                            h2h_matches_count,
                    )
                )


                # =================================================
                # NORMALIZE VALUES
                # =================================================

                pick = (
                    prediction[
                        "pick"
                    ]
                )


                home_probability = (
                    prediction[
                        "probabilities"
                    ][
                        "HOME"
                    ]
                )


                draw_probability = (
                    prediction[
                        "probabilities"
                    ][
                        "DRAW"
                    ]
                )


                away_probability = (
                    prediction[
                        "probabilities"
                    ][
                        "AWAY"
                    ]
                )


                confidence = (
                    prediction[
                        "confidence"
                    ]
                )


                margin = (
                    prediction[
                        "margin"
                    ]
                )


                analitiko_score = (
                    prediction[
                        "analitiko_score"
                    ]
                )


                league_threshold = (
                    prediction[
                        "league_threshold"
                    ]
                )


                elite_threshold = (
                    prediction[
                        "elite_threshold"
                    ]
                )


                is_strong_pick = bool(
                    prediction[
                        "is_strong_pick"
                    ]
                )


                is_elite_pick = bool(
                    prediction[
                        "is_elite_pick"
                    ]
                )


                confidence_level = (
                    prediction[
                        "confidence_level"
                    ]
                )


                # =================================================
                # COUNTERS
                #
                # Counts predictions checked during this run,
                # including unchanged snapshots.
                # =================================================

                if is_strong_pick:
                    strong_count += 1


                if is_elite_pick:
                    elite_count += 1


                # =================================================
                # DISPLAY PREDICTION
                # =================================================

                print(
                    f"Pick: "
                    f"{pick}"
                )

                print(
                    f"Confidence: "
                    f"{confidence}%"
                )

                print(
                    f"Margin: "
                    f"{margin}%"
                )

                print(
                    f"Analitiko Score: "
                    f"{analitiko_score}"
                )

                print(
                    f"League threshold: "
                    f"{league_threshold}"
                )

                print(
                    f"Elite threshold: "
                    f"{elite_threshold}"
                )

                print(
                    f"Strong: "
                    f"{is_strong_pick}"
                )

                print(
                    f"Elite: "
                    f"{is_elite_pick}"
                )

                print(
                    f"Level: "
                    f"{confidence_level}"
                )


                # =================================================
                # CHECK EXISTING SNAPSHOT
                # =================================================

                latest_snapshot = (
                    db.query(
                        MLPredictionSnapshot
                    )
                    .filter(
                        MLPredictionSnapshot.match_id
                        == match.id
                    )
                    .order_by(
                        MLPredictionSnapshot
                        .created_at
                        .desc()
                    )
                    .first()
                )


                if latest_snapshot:

                    same_prediction = (

                        latest_snapshot.model_version
                        == MODEL_VERSION

                        and

                        latest_snapshot.pick
                        == pick

                        and

                        latest_snapshot.home_probability
                        == home_probability

                        and

                        latest_snapshot.draw_probability
                        == draw_probability

                        and

                        latest_snapshot.away_probability
                        == away_probability

                        and

                        latest_snapshot.confidence
                        == confidence

                        and

                        latest_snapshot.margin
                        == margin

                        and

                        latest_snapshot.analitiko_score
                        == analitiko_score

                        and

                        latest_snapshot.league_threshold
                        == league_threshold

                        and

                        latest_snapshot.is_strong_pick
                        == is_strong_pick

                        and

                        latest_snapshot.elite_threshold
                        == elite_threshold

                        and

                        latest_snapshot.is_elite_pick
                        == is_elite_pick

                        and

                        latest_snapshot.confidence_level
                        == confidence_level
                    )


                    if same_prediction:

                        unchanged += 1

                        print(
                            "Snapshot: unchanged"
                        )

                        continue


                # =================================================
                # SAVE NEW SNAPSHOT
                # =================================================

                snapshot = (
                    MLPredictionSnapshot(
                        match_id=
                            match.id,

                        model_version=
                            MODEL_VERSION,

                        league=
                            match.league.name,

                        pick=
                            pick,

                        home_probability=
                            home_probability,

                        draw_probability=
                            draw_probability,

                        away_probability=
                            away_probability,

                        confidence=
                            confidence,

                        margin=
                            margin,

                        analitiko_score=
                            analitiko_score,

                        league_threshold=
                            league_threshold,

                        is_strong_pick=
                            is_strong_pick,

                        elite_threshold=
                            elite_threshold,

                        is_elite_pick=
                            is_elite_pick,

                        confidence_level=
                            confidence_level,
                    )
                )


                db.add(
                    snapshot
                )


                db.commit()


                saved += 1


                print(
                    "Snapshot: SAVED"
                )


            # =====================================================
            # MATCH FAILURE
            # =====================================================

            except Exception as error:

                db.rollback()

                failed += 1


                print(
                    f"FAILED: "
                    f"{error}"
                )


        # =====================================================
        # SUMMARY
        # =====================================================

        print()
        print("=" * 70)
        print(
            "ML SNAPSHOT COMPLETE"
        )
        print("=" * 70)


        print(
            f"Saved: "
            f"{saved}"
        )


        print(
            f"Unchanged: "
            f"{unchanged}"
        )


        print(
            f"Skipped: "
            f"{skipped}"
        )


        print(
            f"Failed: "
            f"{failed}"
        )


        print()
        print(
            f"Strong predictions checked: "
            f"{strong_count}"
        )


        print(
            f"Elite predictions checked: "
            f"{elite_count}"
        )


        print("=" * 70)


    finally:

        db.close()


if __name__ == "__main__":
    run()