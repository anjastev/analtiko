from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db

from app.models.match import Match
from app.models.match_stats import MatchStats
from app.models.odds import Odds
from app.models.team_match_history import TeamMatchHistory

from app.schemas.match import MatchResponse
from app.schemas.match_stats import MatchStatsResponse
from app.schemas.odds import OddsResponse

from app.analytics.popularity import (
    calculate_odds_movement_score,
    calculate_form_score,
    calculate_goals_score,
    calculate_xg_score,
    calculate_popularity_score,
)

from app.analytics.team_form import (
    calculate_form_from_history,
)

from app.predictions.engine import (
    calculate_match_prediction,
)

from app.collectors.api_football import APIFootballClient

from app.services.h2h_service import (
    get_or_fetch_h2h,
)

from app.analytics.h2h import (
    calculate_h2h_summary,
    calculate_h2h_scores,
)
from app.models.h2h import H2HMatch
from app.ml.ml_predictor import predict_result
router = APIRouter(
    prefix="/api/matches",
    tags=["Matches"],
)


# ============================================================
# ALL MATCHES
# ============================================================

@router.get(
    "",
    response_model=list[MatchResponse],
)
def get_matches(
    db: Session = Depends(get_db),
):
    return (
        db.query(Match)
        .order_by(Match.match_date.asc())
        .all()
    )


# ============================================================
# ALL PREDICTIONS
#
# IMPORTANT:
# Овој endpoint мора да биде ПРЕД /{match_id}
# ============================================================

@router.get("/predictions/all")
def get_all_predictions(
    db: Session = Depends(get_db),
):
    matches = (
        db.query(Match)
        .order_by(Match.match_date.asc())
        .all()
    )

    results = []

    for match in matches:

        # ----------------------------------------------------
        # ODDS
        # ----------------------------------------------------

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
            continue

        # ----------------------------------------------------
        # HOME HISTORY
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # AWAY HISTORY
        # ----------------------------------------------------

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
            continue

        home_form_data = (
            calculate_form_from_history(
                home_history
            )
        )

        away_form_data = (
            calculate_form_from_history(
                away_history
            )
        )

        # ----------------------------------------------------
        # OPTIONAL ADVANCED STATS
        # ----------------------------------------------------

        stats = (
            db.query(MatchStats)
            .filter(
                MatchStats.match_id == match.id
            )
            .first()
        )

        # Neutral fallback if real xG is unavailable
        home_xg = 1.2
        away_xg = 1.2

        if stats:
            if stats.home_xg_avg > 0:
                home_xg = stats.home_xg_avg

            if stats.away_xg_avg > 0:
                away_xg = stats.away_xg_avg

        # ----------------------------------------------------
        # PREDICTION
        # ----------------------------------------------------

        prediction = calculate_match_prediction(
            home_form=home_form_data[
                "form_score"
            ],

            away_form=away_form_data[
                "form_score"
            ],

            home_goals=home_form_data[
                "goals_for_avg"
            ],

            away_goals=away_form_data[
                "goals_for_avg"
            ],

            home_xg=home_xg,
            away_xg=away_xg,


        )

        results.append(
            {
                "match_id": match.id,

                "league": match.league.name,

                "home_team":
                    match.home_team.name,

                "away_team":
                    match.away_team.name,

                "match_date":
                    match.match_date,

                "prediction":
                    prediction,
            }
        )

    results.sort(
        key=lambda item:
            item["prediction"][
                "confidence"
            ],
        reverse=True,
    )

    return results


# ============================================================
# MATCH STATS
# ============================================================

@router.get(
    "/{match_id}/stats",
    response_model=MatchStatsResponse,
)
def get_match_stats(
    match_id: int,
    db: Session = Depends(get_db),
):
    stats = (
        db.query(MatchStats)
        .filter(
            MatchStats.match_id == match_id
        )
        .first()
    )

    if not stats:
        raise HTTPException(
            status_code=404,
            detail="Stats not found",
        )

    return stats


# ============================================================
# MATCH ODDS
# ============================================================

@router.get(
    "/{match_id}/odds",
    response_model=list[OddsResponse],
)
def get_match_odds(
    match_id: int,
    db: Session = Depends(get_db),
):
    odds = (
        db.query(Odds)
        .filter(
            Odds.match_id == match_id
        )
        .order_by(
            Odds.recorded_at.asc()
        )
        .all()
    )

    return odds


# ============================================================
# MATCH FORM
# ============================================================

@router.get("/{match_id}/form")
def get_match_form(
    match_id: int,
    db: Session = Depends(get_db),
):
    match = (
        db.query(Match)
        .filter(
            Match.id == match_id
        )
        .first()
    )

    if not match:
        raise HTTPException(
            status_code=404,
            detail="Match not found",
        )

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

    return {
        "match_id": match.id,

        "home_team": {
            "id": match.home_team.id,
            "name": match.home_team.name,
            **home_form,
        },

        "away_team": {
            "id": match.away_team.id,
            "name": match.away_team.name,
            **away_form,
        },
    }


# ============================================================
# POPULARITY
# ============================================================

@router.get(
    "/{match_id}/popularity"
)
def get_match_popularity(
    match_id: int,
    db: Session = Depends(get_db),
):
    match = (
        db.query(Match)
        .filter(
            Match.id == match_id
        )
        .first()
    )

    if not match:
        raise HTTPException(
            status_code=404,
            detail="Match not found",
        )

    # ========================================================
    # HISTORY
    # ========================================================

    home_history = (
        db.query(
            TeamMatchHistory
        )
        .filter(
            TeamMatchHistory.team_id
            == match.home_team_id
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
            == match.away_team_id
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
        or not away_history
    ):
        raise HTTPException(
            status_code=404,
            detail=(
                "Not enough historical data"
            ),
        )

    home_form_data = (
        calculate_form_from_history(
            home_history
        )
    )

    away_form_data = (
        calculate_form_from_history(
            away_history
        )
    )

    # ========================================================
    # ODDS
    # ========================================================

    odds = (
        db.query(Odds)
        .filter(
            Odds.match_id
            == match.id
        )
        .order_by(
            Odds.recorded_at.asc()
        )
        .all()
    )

    if not odds:
        raise HTTPException(
            status_code=404,
            detail="Odds not found",
        )

    opening = odds[0]
    current = odds[-1]

    odds_score = (
        calculate_odds_movement_score(
            opening.home_win,
            current.home_win,

            opening.draw,
            current.draw,

            opening.away_win,
            current.away_win,
        )
    )

    favorite_drop_score = (
        calculate_favorite_drop_score(
            opening.home_win,
            current.home_win,

            opening.away_win,
            current.away_win,
        )
    )

    # ========================================================
    # FORM
    # ========================================================

    form_score = (
        calculate_form_score(
            home_form_data[
                "form_score"
            ],
            away_form_data[
                "form_score"
            ],
        )
    )

    # ========================================================
    # GOALS
    # ========================================================

    goals_score = (
        calculate_goals_score(
            home_form_data[
                "goals_for_avg"
            ],

            away_form_data[
                "goals_for_avg"
            ],
        )
    )

    # ========================================================
    # H2H
    # ========================================================

    home_external_id = (
        match.home_team.external_id
    )

    away_external_id = (
        match.away_team.external_id
    )

    h2h_matches = []

    if (
        home_external_id
        and away_external_id
    ):
        h2h_matches = (
            db.query(H2HMatch)
            .filter(
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

    if h2h_matches:
        h2h_scores = (
            calculate_h2h_scores(
                matches=h2h_matches,
                home_team_external_id=
                    home_external_id,
            )
        )

        h2h_interest = (
            calculate_h2h_interest_score(
                h2h_scores[
                    "home_score"
                ],
                h2h_scores[
                    "away_score"
                ],
            )
        )

    else:
        h2h_interest = 50.0

    # ========================================================
    # PREDICTION CONFIDENCE
    # ========================================================

    latest_odds = current

    home_xg = 1.2
    away_xg = 1.2

    stats = (
        db.query(MatchStats)
        .filter(
            MatchStats.match_id
            == match.id
        )
        .first()
    )

    if stats:
        if (
            stats.home_xg_avg
            > 0
        ):
            home_xg = (
                stats.home_xg_avg
            )

        if (
            stats.away_xg_avg
            > 0
        ):
            away_xg = (
                stats.away_xg_avg
            )

    prediction = (
        calculate_match_prediction(
            home_form=
                home_form_data[
                    "form_score"
                ],

            away_form=
                away_form_data[
                    "form_score"
                ],

            home_goals=
                home_form_data[
                    "goals_for_avg"
                ],

            away_goals=
                away_form_data[
                    "goals_for_avg"
                ],

            home_xg=
                home_xg,

            away_xg=
                away_xg,


        )
    )

    prediction_confidence = (
        prediction["confidence"]
    )

    # ========================================================
    # LEAGUE WEIGHT
    # ========================================================

    league_weights = {
        "Premier League": 95,

        "La Liga": 90,

        "Serie A": 87,

        "Bundesliga": 87,

        "Ligue 1": 82,

        "UEFA Champions League":
            100,

        "UEFA Europa League":
            92,

        "UEFA Conference League":
            80,
    }

    league_weight = (
        league_weights.get(
            match.league.name,
            65,
        )
    )

    # ========================================================
    # FINAL SCORE
    # ========================================================

    popularity_score = (
        calculate_popularity_score(
            odds_score=
                odds_score,

            favorite_drop_score=
                favorite_drop_score,

            prediction_confidence=
                prediction_confidence,

            form_score=
                form_score,

            goals_score=
                goals_score,

            h2h_score=
                h2h_interest,

            league_weight=
                league_weight,
        )
    )

    if popularity_score >= 85:
        level = "very_high"

    elif popularity_score >= 70:
        level = "high"

    elif popularity_score >= 50:
        level = "medium"

    else:
        level = "low"

    return {
        "match_id":
            match.id,

        "popularity_score":
            popularity_score,

        "level":
            level,

        "prediction_confidence":
            prediction_confidence,

        "breakdown": {
            "odds_movement":
                round(
                    odds_score,
                    1,
                ),

            "favorite_drop":
                round(
                    favorite_drop_score,
                    1,
                ),

            "confidence":
                round(
                    prediction_confidence,
                    1,
                ),

            "form":
                round(
                    form_score,
                    1,
                ),

            "goals":
                round(
                    goals_score,
                    1,
                ),

            "h2h":
                round(
                    h2h_interest,
                    1,
                ),

            "league":
                league_weight,
        },
    }
# ============================================================
# PREDICTION
# ============================================================

@router.get(
    "/{match_id}/prediction"
)
def get_match_prediction(
    match_id: int,
    db: Session = Depends(get_db),
):
    match = (
        db.query(Match)
        .filter(
            Match.id == match_id
        )
        .first()
    )

    if not match:
        raise HTTPException(
            status_code=404,
            detail="Match not found",
        )

    # --------------------------------------------------------
    # LATEST ODDS
    # --------------------------------------------------------

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
        raise HTTPException(
            status_code=404,
            detail="Odds not found",
        )

    # --------------------------------------------------------
    # HOME HISTORY
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # AWAY HISTORY
    # --------------------------------------------------------

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
        raise HTTPException(
            status_code=404,
            detail=(
                "Not enough historical "
                "data for prediction"
            ),
        )

    home_form_data = (
        calculate_form_from_history(
            home_history
        )
    )

    away_form_data = (
        calculate_form_from_history(
            away_history
        )
    )

    # --------------------------------------------------------
    # OPTIONAL ADVANCED STATS
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # RUN MODEL
    # --------------------------------------------------------
    # --------------------------------------------------------
    # LOCAL H2H
    # --------------------------------------------------------

    home_external_id = (
        match.home_team.external_id
    )

    away_external_id = (
        match.away_team.external_id
    )

    h2h_matches = []

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

    h2h_scores = (
        calculate_h2h_scores(
            matches=h2h_matches,
            home_team_external_id=
            home_external_id,
        )

        if home_external_id

        else {
            "home_score": 5.0,
            "away_score": 5.0,
        }
    )

    prediction = (
        calculate_match_prediction(

            home_form=
            home_form_data[
                "form_score"
            ],

            away_form=
            away_form_data[
                "form_score"
            ],

            home_goals=
            home_form_data[
                "goals_for_avg"
            ],

            away_goals=
            away_form_data[
                "goals_for_avg"
            ],

            home_xg=
            home_xg,

            away_xg=
            away_xg,



            home_h2h_score=
            h2h_scores[
                "home_score"
            ],

            away_h2h_score=
            h2h_scores[
                "away_score"
            ],
        )
    )

    # --------------------------------------------------------
    # REASONS
    # --------------------------------------------------------

    reasons = []

    if (
        home_form_data["form_score"]
        >
        away_form_data["form_score"]
    ):
        reasons.append(
            f"{match.home_team.name} "
            f"has better recent form."
        )

    elif (
        away_form_data["form_score"]
        >
        home_form_data["form_score"]
    ):
        reasons.append(
            f"{match.away_team.name} "
            f"has better recent form."
        )

    if (
        home_form_data[
            "goals_for_avg"
        ]
        >
        away_form_data[
            "goals_for_avg"
        ]
    ):
        reasons.append(
            f"{match.home_team.name} "
            f"has a higher recent "
            f"goals-per-match average."
        )

    elif (
        away_form_data[
            "goals_for_avg"
        ]
        >
        home_form_data[
            "goals_for_avg"
        ]
    ):
        reasons.append(
            f"{match.away_team.name} "
            f"has a higher recent "
            f"goals-per-match average."
        )

    if (
        prediction["over_25"]
        >= 65
    ):
        reasons.append(
            "Recent scoring signals "
            "support a higher-scoring match."
        )

    if (
        prediction["btts_yes"]
        >= 65
    ):
        reasons.append(
            "Both teams show a relatively "
            "strong scoring signal."
        )

    if h2h_matches:

        if (
                h2h_scores["home_score"]
                >
                h2h_scores["away_score"]
        ):
            reasons.append(
                f"{match.home_team.name} "
                f"has the stronger recent "
                f"head-to-head record."
            )

        elif (
                h2h_scores["away_score"]
                >
                h2h_scores["home_score"]
        ):
            reasons.append(
                f"{match.away_team.name} "
                f"has the stronger recent "
                f"head-to-head record."
            )



    return {
        "match_id":
            match.id,

        "prediction":
            prediction,

        "reasons":
            reasons,
    }


# ============================================================
# SINGLE MATCH
#
# IMPORTANT:
# Овој endpoint нека биде најдолу.
# ============================================================


# ============================================================
# HEAD TO HEAD
# ============================================================

@router.get("/{match_id}/h2h")
def get_match_h2h(
    match_id: int,
    db: Session = Depends(get_db),
):
    match = (
        db.query(Match)
        .filter(
            Match.id == match_id
        )
        .first()
    )

    if not match:
        raise HTTPException(
            status_code=404,
            detail="Match not found",
        )

    home_external_id = (
        match.home_team.external_id
    )

    away_external_id = (
        match.away_team.external_id
    )

    if (
        not home_external_id
        or not away_external_id
    ):
        raise HTTPException(
            status_code=404,
            detail="Missing external team IDs",
        )

    client = APIFootballClient()

    h2h_matches = get_or_fetch_h2h(
        db=db,
        client=client,
        team_a_id=home_external_id,
        team_b_id=away_external_id,
        limit=5,
    )

    summary = calculate_h2h_summary(
        matches=h2h_matches,
        home_team_external_id=home_external_id,
    )

    return {
        "match_id": match.id,

        "home_team": match.home_team.name,
        "away_team": match.away_team.name,

        "summary": summary,

        "matches": [
            {
                "date": row.match_date,
                "home_team": row.home_team_name,
                "away_team": row.away_team_name,
                "home_goals": row.home_goals,
                "away_goals": row.away_goals,
            }
            for row in h2h_matches
        ],
    }
@router.get("/trending/all")
def get_trending_matches(
    db: Session = Depends(get_db),
):
    matches = (
        db.query(Match)
        .order_by(Match.match_date.asc())
        .all()
    )

    results = []

    league_weights = {
        "Premier League": 95,
        "La Liga": 90,
        "Serie A": 87,
        "Bundesliga": 87,
        "Ligue 1": 82,
        "UEFA Champions League": 100,
        "UEFA Europa League": 92,
        "UEFA Conference League": 80,
    }

    for match in matches:

        # =====================================================
        # ODDS
        # =====================================================

        odds = (
            db.query(Odds)
            .filter(
                Odds.match_id == match.id
            )
            .order_by(
                Odds.recorded_at.asc()
            )
            .all()
        )

        if not odds:
            continue

        opening = odds[0]
        current = odds[-1]

        # =====================================================
        # HOME HISTORY
        # =====================================================

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

        # =====================================================
        # AWAY HISTORY
        # =====================================================

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
            continue

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

        # =====================================================
        # ODDS MOVEMENT
        # =====================================================

        odds_score = (
            calculate_odds_movement_score(
                opening.home_win,
                current.home_win,

                opening.draw,
                current.draw,

                opening.away_win,
                current.away_win,
            )
        )

        favorite_drop_score = (
            calculate_favorite_drop_score(
                opening.home_win,
                current.home_win,

                opening.away_win,
                current.away_win,
            )
        )

        # =====================================================
        # FORM
        # =====================================================

        form_score = (
            calculate_form_score(
                home_form["form_score"],
                away_form["form_score"],
            )
        )

        # =====================================================
        # GOALS
        # =====================================================

        goals_score = (
            calculate_goals_score(
                home_form["goals_for_avg"],
                away_form["goals_for_avg"],
            )
        )

        # =====================================================
        # REAL CACHED H2H
        # =====================================================

        home_external_id = (
            match.home_team.external_id
        )

        away_external_id = (
            match.away_team.external_id
        )

        h2h_matches = []

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

            h2h_interest = (
                calculate_h2h_interest_score(
                    h2h_scores["home_score"],
                    h2h_scores["away_score"],
                )
            )

        else:
            h2h_scores = {
                "home_score": 5.0,
                "away_score": 5.0,
            }

            h2h_interest = 50.0

        # =====================================================
        # OPTIONAL xG
        # =====================================================

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

        # =====================================================
        # PREDICTION
        # =====================================================

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

                home_xg=home_xg,
                away_xg=away_xg,



                home_h2h_score=
                    h2h_scores["home_score"],

                away_h2h_score=
                    h2h_scores["away_score"],
            )
        )

        # =====================================================
        # LEAGUE
        # =====================================================

        league_weight = (
            league_weights.get(
                match.league.name,
                65,
            )
        )

        # =====================================================
        # FINAL TRENDING SCORE
        # =====================================================

        score = (
            calculate_popularity_score(
                odds_score=
                    odds_score,

                favorite_drop_score=
                    favorite_drop_score,

                prediction_confidence=
                    prediction["confidence"],

                form_score=
                    form_score,

                goals_score=
                    goals_score,

                h2h_score=
                    h2h_interest,

                league_weight=
                    league_weight,
            )
        )

        # =====================================================
        # MOVEMENT LABEL
        # =====================================================

        home_change = (
            current.home_win
            - opening.home_win
        )

        away_change = (
            current.away_win
            - opening.away_win
        )

        if home_change < 0:
            market_signal = "HOME_DROP"

        elif away_change < 0:
            market_signal = "AWAY_DROP"

        else:
            market_signal = "STABLE"

        # =====================================================
        # RESULT
        # =====================================================

        results.append(
            {
                "match_id":
                    match.id,

                "league":
                    match.league.name,

                "home_team":
                    match.home_team.name,

                "away_team":
                    match.away_team.name,

                "match_date":
                    match.match_date,

                "score":
                    score,

                "confidence":
                    prediction["confidence"],

                "main_pick":
                    prediction["main_pick"],

                "market_signal":
                    market_signal,

                "h2h": {
                    "matches":
                        len(h2h_matches),

                    "home_score":
                        h2h_scores["home_score"],

                    "away_score":
                        h2h_scores["away_score"],
                },

                "form": {
                    "home":
                        home_form["form_score"],

                    "away":
                        away_form["form_score"],
                },

                "odds": {
                    "home":
                        current.home_win,

                    "draw":
                        current.draw,

                    "away":
                        current.away_win,
                },

                "breakdown": {
                    "odds_movement":
                        round(
                            odds_score,
                            1,
                        ),

                    "favorite_drop":
                        round(
                            favorite_drop_score,
                            1,
                        ),

                    "form":
                        round(
                            form_score,
                            1,
                        ),

                    "goals":
                        round(
                            goals_score,
                            1,
                        ),

                    "h2h":
                        round(
                            h2h_interest,
                            1,
                        ),

                    "league":
                        league_weight,
                },
            }
        )

    # =========================================================
    # SORT
    # =========================================================

    results.sort(
        key=lambda item:
            item["score"],
        reverse=True,
    )

    return results


@router.get("/market-movers/all")
def get_market_movers(
    db: Session = Depends(get_db),
):
    matches = (
        db.query(Match)
        .order_by(Match.match_date.asc())
        .all()
    )

    results = []

    for match in matches:
        odds = (
            db.query(Odds)
            .filter(
                Odds.match_id == match.id
            )
            .order_by(
                Odds.recorded_at.asc()
            )
            .all()
        )

        if len(odds) < 2:
            continue

        opening = odds[0]
        current = odds[-1]

        markets = [
            (
                "HOME",
                opening.home_win,
                current.home_win,
            ),
            (
                "DRAW",
                opening.draw,
                current.draw,
            ),
            (
                "AWAY",
                opening.away_win,
                current.away_win,
            ),
        ]

        for (
            market_name,
            opening_odd,
            current_odd,
        ) in markets:

            if (
                opening_odd is None
                or current_odd is None
                or opening_odd <= 0
            ):
                continue

            change = (
                current_odd
                - opening_odd
            )

            change_percentage = (
                change
                / opening_odd
            ) * 100

            direction = (
                "DROP"
                if change < 0
                else "RISE"
            )

            results.append(
                {
                    "match_id":
                        match.id,

                    "league":
                        match.league.name,

                    "home_team":
                        match.home_team.name,

                    "away_team":
                        match.away_team.name,

                    "match_date":
                        match.match_date,

                    "market":
                        market_name,

                    "opening_odd":
                        round(
                            opening_odd,
                            2,
                        ),

                    "current_odd":
                        round(
                            current_odd,
                            2,
                        ),

                    "change":
                        round(
                            change,
                            2,
                        ),

                    "change_percentage":
                        round(
                            change_percentage,
                            2,
                        ),

                    "direction":
                        direction,
                }
            )

    results.sort(
        key=lambda item:
            abs(
                item[
                    "change_percentage"
                ]
            ),
        reverse=True,
    )

    return results



@router.get("/{match_id}/ml-prediction")
def get_match_ml_prediction(
    match_id: int,
    db: Session = Depends(get_db),
):
    match = (
        db.query(Match)
        .filter(
            Match.id == match_id
        )
        .first()
    )

    if not match:
        raise HTTPException(
            status_code=404,
            detail="Match not found",
        )

    # ========================================================
    # ODDS
    # ========================================================

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
        raise HTTPException(
            status_code=404,
            detail="Odds not found",
        )

    # ========================================================
    # HISTORY
    # ========================================================

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
        raise HTTPException(
            status_code=404,
            detail="Historical data not found",
        )

    home_form = calculate_form_from_history(
        home_history
    )

    away_form = calculate_form_from_history(
        away_history
    )

    # ========================================================
    # XG
    # ========================================================

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

    # ========================================================
    # H2H
    # ========================================================

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

        h2h_matches_count = len(
            h2h_matches
        )

        if h2h_matches:
            h2h_scores = calculate_h2h_scores(
                matches=h2h_matches,
                home_team_external_id=
                    home_external_id,
            )

            h2h_home_score = (
                h2h_scores["home_score"]
            )

            h2h_away_score = (
                h2h_scores["away_score"]
            )

    # ========================================================
    # ML PREDICTION
    # ========================================================

    ml_prediction = predict_result(
        league=
            match.league.name,

        home_form=
            home_form["form_score"],

        away_form=
            away_form["form_score"],

        home_goals_avg=
            home_form["goals_for_avg"],

        away_goals_avg=
            away_form["goals_for_avg"],

        home_goals_against_avg=
            home_form["goals_against_avg"],

        away_goals_against_avg=
            away_form["goals_against_avg"],

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

    return {
        "match_id": match.id,

        "home_team":
            match.home_team.name,

        "away_team":
            match.away_team.name,

        "league":
            match.league.name,

        "model":
            "logistic_regression_v2",

        "experimental":
            True,

        "training_warning": (
            "Experimental ML model trained on historical "
            "multi-league data. League-specific strong-pick "
            "thresholds are based on walk-forward validation."
        ),

        "prediction":
            ml_prediction,
    }

@router.get("/{match_id}/prediction-comparison")
def get_prediction_comparison(
    match_id: int,
    db: Session = Depends(get_db),
):
    match = (
        db.query(Match)
        .filter(
            Match.id == match_id
        )
        .first()
    )

    if not match:
        raise HTTPException(
            status_code=404,
            detail="Match not found",
        )

    # ========================================================
    # ODDS
    # ========================================================

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
        raise HTTPException(
            status_code=404,
            detail="Odds not found",
        )

    # ========================================================
    # HISTORY
    # ========================================================

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
        raise HTTPException(
            status_code=404,
            detail="Historical data not found",
        )

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

    # ========================================================
    # XG
    # ========================================================

    stats = (
        db.query(MatchStats)
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
            and stats.home_xg_avg > 0
        ):
            home_xg = (
                stats.home_xg_avg
            )

        if (
            stats.away_xg_avg
            and stats.away_xg_avg > 0
        ):
            away_xg = (
                stats.away_xg_avg
            )

    # ========================================================
    # H2H
    # ========================================================

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

        h2h_matches_count = (
            len(h2h_matches)
        )

        if h2h_matches:

            h2h_scores = (
                calculate_h2h_scores(
                    matches=h2h_matches,
                    home_team_external_id=
                        home_external_id,
                )
            )

            h2h_home_score = (
                h2h_scores[
                    "home_score"
                ]
            )

            h2h_away_score = (
                h2h_scores[
                    "away_score"
                ]
            )

    # ========================================================
    # RULE ENGINE
    # ========================================================

    rule_prediction = (
        calculate_match_prediction(
            home_form=
                home_form[
                    "form_score"
                ],

            away_form=
                away_form[
                    "form_score"
                ],

            home_goals=
                home_form[
                    "goals_for_avg"
                ],

            away_goals=
                away_form[
                    "goals_for_avg"
                ],

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
                h2h_home_score,

            away_h2h_score=
                h2h_away_score,
        )
    )

    # ========================================================
    # ML MODEL
    # ========================================================

    ml_prediction = (
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

    # ========================================================
    # COMPARISON
    # ========================================================

    rule_pick = (
        rule_prediction[
            "main_pick"
        ]
    )

    ml_pick = (
        ml_prediction[
            "pick"
        ]
    )

    agreement = (
        rule_pick
        == ml_pick
    )

    rule_probability_key = {
        "HOME":
            "home_win",

        "DRAW":
            "draw",

        "AWAY":
            "away_win",
    }

    rule_selected_probability = (
        rule_prediction[
            rule_probability_key[
                rule_pick
            ]
        ]
    )

    ml_selected_probability = (
        ml_prediction[
            "probabilities"
        ].get(
            ml_pick,
            0.0,
        )
    )

    probability_difference = (
        round(
            abs(
                rule_selected_probability
                -
                ml_selected_probability
            ),
            1,
        )
    )

    # ========================================================
    # RETURN
    # ========================================================

    return {
        "match_id":
            match.id,

        "home_team":
            match.home_team.name,

        "away_team":
            match.away_team.name,

        "league":
            match.league.name,

        "rule_engine": {
            "pick":
                rule_pick,

            "confidence":
                rule_prediction[
                    "confidence"
                ],

            "probabilities": {
                "HOME":
                    rule_prediction[
                        "home_win"
                    ],

                "DRAW":
                    rule_prediction[
                        "draw"
                    ],

                "AWAY":
                    rule_prediction[
                        "away_win"
                    ],
            },

            "over_25":
                rule_prediction[
                    "over_25"
                ],

            "btts_yes":
                rule_prediction[
                    "btts_yes"
                ],
        },

        "ml_model": {
            "pick":
                ml_pick,

            "probabilities":
                ml_prediction[
                    "probabilities"
                ],

            "confidence":
                ml_prediction[
                    "confidence"
                ],

            "margin":
                ml_prediction[
                    "margin"
                ],

            "analitiko_score":
                ml_prediction[
                    "analitiko_score"
                ],

            "league_threshold":
                ml_prediction[
                    "league_threshold"
                ],

            "is_strong_pick":
                ml_prediction[
                    "is_strong_pick"
                ],

            "confidence_level":
                ml_prediction[
                    "confidence_level"
                ],

            "trained_classes":
                ml_prediction[
                    "trained_classes"
                ],

            "experimental":
                ml_prediction.get(
                    "experimental",
                    True,
                ),
        },

        "comparison": {
            "agreement":
                agreement,

            "same_pick":
                agreement,

            "rule_selected_probability":
                rule_selected_probability,

            "ml_selected_probability":
                ml_selected_probability,

            "probability_difference":
                probability_difference,
        },

        "warning": (
            "ML predictions are experimental. "
            "League-specific strong-pick thresholds "
            "are derived from historical walk-forward "
            "validation and do not guarantee future results."
        ),
    }


@router.get("/ml-predictions/all")
def get_all_ml_predictions(
    db: Session = Depends(get_db),
):
    matches = (
        db.query(Match)
        .order_by(
            Match.match_date.asc()
        )
        .all()
    )

    results = []

    for match in matches:

        home_history = (
            db.query(
                TeamMatchHistory
            )
            .filter(
                TeamMatchHistory.team_id
                == match.home_team_id
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
                == match.away_team_id
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
            or not away_history
        ):
            continue


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


        stats = (
            db.query(MatchStats)
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
                and stats.home_xg_avg > 0
            ):
                home_xg = (
                    stats.home_xg_avg
                )

            if (
                stats.away_xg_avg
                and stats.away_xg_avg > 0
            ):
                away_xg = (
                    stats.away_xg_avg
                )


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

                h2h_scores = (
                    calculate_h2h_scores(
                        matches=
                            h2h_matches,

                        home_team_external_id=
                            home_external_id,
                    )
                )


                h2h_home_score = (
                    h2h_scores[
                        "home_score"
                    ]
                )

                h2h_away_score = (
                    h2h_scores[
                        "away_score"
                    ]
                )


        ml_prediction = (
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


        results.append(
            {
                "match_id":
                    match.id,

                "league":
                    match.league.name,

                "home_team":
                    match.home_team.name,

                "away_team":
                    match.away_team.name,

                "match_date":
                    match.match_date,

                "status":
                    match.status,

                "prediction":
                    ml_prediction,
            }
        )


    results.sort(
        key=lambda item:
            (
                item[
                    "prediction"
                ][
                    "analitiko_score"
                ]
            ),
        reverse=True,
    )


    return results



@router.get(
    "/{match_id}",
    response_model=MatchResponse,
)
def get_match(
    match_id: int,
    db: Session = Depends(get_db),
):
    match = (
        db.query(Match)
        .filter(
            Match.id == match_id
        )
        .first()
    )

    if not match:
        raise HTTPException(
            status_code=404,
            detail="Match not found",
        )

    return match