from sqlalchemy.orm import Session

from app.models.match import Match
from app.models.odds import Odds
from app.models.match_stats import MatchStats
from app.models.team_match_history import TeamMatchHistory
from app.models.h2h import H2HMatch
from app.models.prediction_snapshot import PredictionSnapshot

from app.analytics.team_form import (
    calculate_form_from_history,
)

from app.analytics.h2h import (
    calculate_h2h_scores,
)

from app.predictions.engine import (
    calculate_match_prediction,
)


CONFIDENCE_CHANGE_THRESHOLD = 2.0


def create_prediction_snapshot(
    db: Session,
    match: Match,
) -> tuple[PredictionSnapshot | None, str]:

    # =========================================================
    # ODDS
    # =========================================================

    latest_odds = (
        db.query(Odds)
        .filter(
            Odds.match_id == match.id
        )
        .order_by(
            Odds.recorded_at.desc()
        )
        .first()
    )

    if not latest_odds:
        return None, "no_odds"

    # =========================================================
    # HISTORY
    # =========================================================

    home_history = (
        db.query(TeamMatchHistory)
        .filter(
            TeamMatchHistory.team_id
            == match.home_team_id
        )
        .order_by(
            TeamMatchHistory.match_date.desc()
        )
        .limit(5)
        .all()
    )

    away_history = (
        db.query(TeamMatchHistory)
        .filter(
            TeamMatchHistory.team_id
            == match.away_team_id
        )
        .order_by(
            TeamMatchHistory.match_date.desc()
        )
        .limit(5)
        .all()
    )

    if not home_history or not away_history:
        return None, "no_history"

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

    # =========================================================
    # OPTIONAL XG
    # =========================================================

    stats = (
        db.query(MatchStats)
        .filter(
            MatchStats.match_id == match.id
        )
        .first()
    )

    home_xg = 1.2
    away_xg = 1.2

    if stats:
        if stats.home_xg_avg > 0:
            home_xg = stats.home_xg_avg

        if stats.away_xg_avg > 0:
            away_xg = stats.away_xg_avg

    # =========================================================
    # H2H
    # =========================================================

    home_external_id = (
        match.home_team.external_id
    )

    away_external_id = (
        match.away_team.external_id
    )

    h2h_scores = {
        "home_score": 5.0,
        "away_score": 5.0,
    }

    if (
        home_external_id
        and away_external_id
    ):
        h2h_matches = (
            db.query(H2HMatch)
            .filter(
                (
                    (
                        H2HMatch.home_team_external_id
                        == home_external_id
                    )
                    &
                    (
                        H2HMatch.away_team_external_id
                        == away_external_id
                    )
                )
                |
                (
                    (
                        H2HMatch.home_team_external_id
                        == away_external_id
                    )
                    &
                    (
                        H2HMatch.away_team_external_id
                        == home_external_id
                    )
                )
            )
            .order_by(
                H2HMatch.match_date.desc()
            )
            .limit(5)
            .all()
        )

        if h2h_matches:
            h2h_scores = (
                calculate_h2h_scores(
                    matches=h2h_matches,
                    home_team_external_id=
                        home_external_id,
                )
            )

    # =========================================================
    # CALCULATE CURRENT PREDICTION
    # =========================================================

    prediction = (
        calculate_match_prediction(
            home_form=
                home_form["form_score"],

            away_form=
                away_form["form_score"],

            home_goals=
                home_form["goals_for_avg"],

            away_goals=
                away_form["goals_for_avg"],

            home_xg=
                home_xg,

            away_xg=
                away_xg,

            home_odds=
                latest_odds.home_win,

            draw_odds=
                latest_odds.draw,

            away_odds=
                latest_odds.away_win,

            home_h2h_score=
                h2h_scores["home_score"],

            away_h2h_score=
                h2h_scores["away_score"],
        )
    )

    # =========================================================
    # GET LAST SNAPSHOT
    # =========================================================

    latest_snapshot = (
        db.query(PredictionSnapshot)
        .filter(
            PredictionSnapshot.match_id
            == match.id
        )
        .order_by(
            PredictionSnapshot.created_at.desc()
        )
        .first()
    )

    # =========================================================
    # SMART DUPLICATE CHECK
    # =========================================================

    if latest_snapshot:

        same_pick = (
            latest_snapshot.main_pick
            == prediction["main_pick"]
        )

        confidence_difference = abs(
            latest_snapshot.confidence
            - prediction["confidence"]
        )

        home_difference = abs(
            latest_snapshot.home_win
            - prediction["home_win"]
        )

        draw_difference = abs(
            latest_snapshot.draw
            - prediction["draw"]
        )

        away_difference = abs(
            latest_snapshot.away_win
            - prediction["away_win"]
        )

        probabilities_stable = (
            home_difference < 2
            and draw_difference < 2
            and away_difference < 2
        )

        if (
            same_pick
            and confidence_difference
            < CONFIDENCE_CHANGE_THRESHOLD
            and probabilities_stable
        ):
            return (
                latest_snapshot,
                "unchanged",
            )

    # =========================================================
    # SAVE NEW SNAPSHOT
    # =========================================================

    snapshot = PredictionSnapshot(
        match_id=
            match.id,

        main_pick=
            prediction["main_pick"],

        confidence=
            prediction["confidence"],

        home_win=
            prediction["home_win"],

        draw=
            prediction["draw"],

        away_win=
            prediction["away_win"],

        over_25=
            prediction["over_25"],

        btts_yes=
            prediction["btts_yes"],
    )

    db.add(snapshot)
    db.flush()

    return (
        snapshot,
        "saved",
    )