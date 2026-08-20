from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.h2h import H2HMatch
from app.models.match import Match
from app.models.match_stats import MatchStats
from app.models.team_match_history import (
    TeamMatchHistory,
)

from app.analytics.h2h import (
    calculate_h2h_scores,
)
from app.analytics.team_form import (
    calculate_form_from_history,
)


# ============================================================
# CONFIG
# ============================================================

GENERAL_HISTORY_LIMIT = 5
SHORT_HISTORY_LIMIT = 3
VENUE_HISTORY_LIMIT = 10


# ============================================================
# BASIC HELPERS
# ============================================================

def safe_average(
    values: list[float],
) -> float:

    if not values:
        return 0.0

    return round(
        sum(values)
        / len(values),
        4,
    )


def calculate_history_metrics(
    history: list[TeamMatchHistory],
) -> dict:

    if not history:

        return {
            "matches": 0,
            "ppg": 0.0,
            "goals_avg": 0.0,
            "conceded_avg": 0.0,
            "goal_diff_avg": 0.0,
            "clean_sheet_rate": 0.0,
            "failed_score_rate": 0.0,
            "win_rate": 0.0,
        }

    matches = len(
        history
    )

    points = 0
    goals_for = 0
    goals_against = 0
    clean_sheets = 0
    failed_score = 0
    wins = 0

    for item in history:

        goals_for += int(
            item.goals_for
        )

        goals_against += int(
            item.goals_against
        )

        if item.result == "W":
            points += 3
            wins += 1

        elif item.result == "D":
            points += 1

        if item.goals_against == 0:
            clean_sheets += 1

        if item.goals_for == 0:
            failed_score += 1

    return {
        "matches":
            matches,

        "ppg":
            round(
                points / matches,
                4,
            ),

        "goals_avg":
            round(
                goals_for / matches,
                4,
            ),

        "conceded_avg":
            round(
                goals_against / matches,
                4,
            ),

        "goal_diff_avg":
            round(
                (
                    goals_for
                    - goals_against
                )
                / matches,
                4,
            ),

        "clean_sheet_rate":
            round(
                clean_sheets
                / matches,
                4,
            ),

        "failed_score_rate":
            round(
                failed_score
                / matches,
                4,
            ),

        "win_rate":
            round(
                wins
                / matches,
                4,
            ),
    }


# ============================================================
# HISTORY
# ============================================================

def get_team_history(
    db: Session,
    team_id: int,
    before_date,
    limit: int,
    venue: str | None = None,
):

    query = (
        db.query(
            TeamMatchHistory
        )
        .filter(
            TeamMatchHistory.team_id
            == team_id,

            TeamMatchHistory.match_date
            < before_date,
        )
    )

    if venue is not None:

        query = query.filter(
            TeamMatchHistory.venue
            == venue
        )

    return (
        query
        .order_by(
            TeamMatchHistory.match_date
            .desc()
        )
        .limit(
            limit
        )
        .all()
    )


# ============================================================
# H2H
# ============================================================

def get_h2h_features(
    db: Session,
    match: Match,
):

    home_external_id = (
        match.home_team.external_id
    )

    away_external_id = (
        match.away_team.external_id
    )

    default = {
        "h2h_home_score": 5.0,
        "h2h_away_score": 5.0,
        "h2h_matches": 0,
    }

    if (
        not home_external_id
        or not away_external_id
    ):
        return default

    rows = (
        db.query(H2HMatch)
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
            ),
        )
        .order_by(
            H2HMatch.match_date.desc()
        )
        .limit(5)
        .all()
    )

    if not rows:
        return default

    scores = (
        calculate_h2h_scores(
            matches=rows,
            home_team_external_id=(
                home_external_id
            ),
        )
    )

    return {
        "h2h_home_score":
            float(
                scores[
                    "home_score"
                ]
            ),

        "h2h_away_score":
            float(
                scores[
                    "away_score"
                ]
            ),

        "h2h_matches":
            len(rows),
    }


# ============================================================
# FEATURE BUILDER
# ============================================================

def build_football_features_v2(
    db: Session,
    match: Match,
) -> dict | None:

    # ========================================================
    # GENERAL FORM - LAST 5
    # ========================================================

    home_history = (
        get_team_history(
            db=db,
            team_id=(
                match.home_team_id
            ),
            before_date=(
                match.match_date
            ),
            limit=(
                GENERAL_HISTORY_LIMIT
            ),
        )
    )

    away_history = (
        get_team_history(
            db=db,
            team_id=(
                match.away_team_id
            ),
            before_date=(
                match.match_date
            ),
            limit=(
                GENERAL_HISTORY_LIMIT
            ),
        )
    )

    if (
        not home_history
        or not away_history
    ):
        return None

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
    # SHORT FORM - LAST 3
    # ========================================================

    home_history_3 = (
        home_history[
            :SHORT_HISTORY_LIMIT
        ]
    )

    away_history_3 = (
        away_history[
            :SHORT_HISTORY_LIMIT
        ]
    )

    home_form_3 = (
        calculate_form_from_history(
            home_history_3
        )
    )

    away_form_3 = (
        calculate_form_from_history(
            away_history_3
        )
    )

    # ========================================================
    # VENUE HISTORY
    # ========================================================

    home_home_history = (
        get_team_history(
            db=db,
            team_id=(
                match.home_team_id
            ),
            before_date=(
                match.match_date
            ),
            limit=(
                VENUE_HISTORY_LIMIT
            ),
            venue="home",
        )
    )

    away_away_history = (
        get_team_history(
            db=db,
            team_id=(
                match.away_team_id
            ),
            before_date=(
                match.match_date
            ),
            limit=(
                VENUE_HISTORY_LIMIT
            ),
            venue="away",
        )
    )

    home_context = (
        calculate_history_metrics(
            home_home_history
        )
    )

    away_context = (
        calculate_history_metrics(
            away_away_history
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

    # ========================================================
    # H2H
    # ========================================================

    h2h = (
        get_h2h_features(
            db=db,
            match=match,
        )
    )

    # ========================================================
    # RETURN
    # ========================================================

    return {
        # --------------------------------------------
        # V1
        # --------------------------------------------

        "home_form":
            float(
                home_form[
                    "form_score"
                ]
            ),

        "away_form":
            float(
                away_form[
                    "form_score"
                ]
            ),

        "home_goals_avg":
            float(
                home_form[
                    "goals_for_avg"
                ]
            ),

        "away_goals_avg":
            float(
                away_form[
                    "goals_for_avg"
                ]
            ),

        "home_goals_against_avg":
            float(
                home_form[
                    "goals_against_avg"
                ]
            ),

        "away_goals_against_avg":
            float(
                away_form[
                    "goals_against_avg"
                ]
            ),

        "home_xg":
            home_xg,

        "away_xg":
            away_xg,

        "h2h_home_score":
            h2h[
                "h2h_home_score"
            ],

        "h2h_away_score":
            h2h[
                "h2h_away_score"
            ],

        "h2h_matches":
            h2h[
                "h2h_matches"
            ],

        "league":
            match.league.name,

        # --------------------------------------------
        # V2
        # --------------------------------------------

        "home_form_3":
            float(
                home_form_3[
                    "form_score"
                ]
            ),

        "away_form_3":
            float(
                away_form_3[
                    "form_score"
                ]
            ),

        "recent_form_diff_3":
            round(
                float(
                    home_form_3[
                        "form_score"
                    ]
                )
                -
                float(
                    away_form_3[
                        "form_score"
                    ]
                ),
                4,
            ),

        "home_home_ppg":
            home_context[
                "ppg"
            ],

        "away_away_ppg":
            away_context[
                "ppg"
            ],

        "home_home_goals_avg":
            home_context[
                "goals_avg"
            ],

        "away_away_goals_avg":
            away_context[
                "goals_avg"
            ],

        "home_home_conceded_avg":
            home_context[
                "conceded_avg"
            ],

        "away_away_conceded_avg":
            away_context[
                "conceded_avg"
            ],

        "home_home_goal_diff_avg":
            home_context[
                "goal_diff_avg"
            ],

        "away_away_goal_diff_avg":
            away_context[
                "goal_diff_avg"
            ],

        "home_home_clean_sheet_rate":
            home_context[
                "clean_sheet_rate"
            ],

        "away_away_clean_sheet_rate":
            away_context[
                "clean_sheet_rate"
            ],

        "home_home_failed_score_rate":
            home_context[
                "failed_score_rate"
            ],

        "away_away_failed_score_rate":
            away_context[
                "failed_score_rate"
            ],

        "home_home_win_rate":
            home_context[
                "win_rate"
            ],

        "away_away_win_rate":
            away_context[
                "win_rate"
            ],

        "home_away_context_diff":
            round(
                home_context[
                    "ppg"
                ]
                -
                away_context[
                    "ppg"
                ],
                4,
            ),

        # --------------------------------------------
        # QUALITY METADATA
        # Do NOT use as ML features.
        # --------------------------------------------

        "_home_history_count":
            len(home_history),

        "_away_history_count":
            len(away_history),

        "_home_venue_count":
            len(
                home_home_history
            ),

        "_away_venue_count":
            len(
                away_away_history
            ),
    }