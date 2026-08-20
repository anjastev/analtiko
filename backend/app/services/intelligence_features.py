from __future__ import annotations

from datetime import (
    datetime,
    timezone,
)

from sqlalchemy.orm import Session

from app.models.match import Match

from app.services.elo_service import (
    get_team_elo_before,
)

from app.services.market_consensus_service import (
    calculate_full_market_consensus,
)

from app.services.strength_adjusted_form import (
    calculate_strength_adjusted_form,
)


# ============================================================
# DATETIME NORMALIZATION
# ============================================================

def ensure_utc(
    value: datetime | None,
) -> datetime | None:

    if value is None:
        return None

    if value.tzinfo is None:

        return value.replace(
            tzinfo=timezone.utc
        )

    return value.astimezone(
        timezone.utc
    )


# ============================================================
# BUILD FEATURES
# ============================================================

def build_match_features(
    db: Session,
    *,
    match: Match,
    snapshot_at: datetime,
):

    snapshot_at_utc = (
        ensure_utc(
            snapshot_at
        )
    )

    kickoff_utc = (
        ensure_utc(
            match.match_date
        )
    )

    if (
        snapshot_at_utc is None
        or kickoff_utc is None
    ):

        raise ValueError(
            "Missing snapshot or kickoff datetime."
        )

    # ========================================================
    # STRICT ANTI-LEAKAGE
    # ========================================================

    if (
        snapshot_at_utc
        >= kickoff_utc
    ):

        raise ValueError(
            "Feature snapshot must be "
            "created before kickoff."
        )

    # ========================================================
    # IMPORTANT FOR SQLITE
    #
    # DB columns currently contain naive UTC datetimes.
    # Python comparison above uses aware UTC.
    #
    # SQLAlchemy filters below use naive UTC to match the
    # existing SQLite representation.
    # ========================================================

    db_snapshot_at = (
        snapshot_at_utc
        .replace(
            tzinfo=None
        )
    )

    # ========================================================
    # ELO
    # ========================================================

    home_elo = (
        get_team_elo_before(
            db=db,

            team_id=(
                match.home_team_id
            ),

            before_date=(
                db_snapshot_at
            ),
        )
    )

    away_elo = (
        get_team_elo_before(
            db=db,

            team_id=(
                match.away_team_id
            ),

            before_date=(
                db_snapshot_at
            ),
        )
    )

    # ========================================================
    # STRENGTH-ADJUSTED FORM
    # ========================================================

    home_form = (
        calculate_strength_adjusted_form(
            db=db,

            team_id=(
                match.home_team_id
            ),

            before_date=(
                db_snapshot_at
            ),
        )
    )

    away_form = (
        calculate_strength_adjusted_form(
            db=db,

            team_id=(
                match.away_team_id
            ),

            before_date=(
                db_snapshot_at
            ),
        )
    )

    # ========================================================
    # MARKET CONSENSUS
    # ========================================================

    market = (
        calculate_full_market_consensus(
            db=db,

            match_id=(
                match.id
            ),

            market_code="1X2",

            snapshot_at=(
                db_snapshot_at
            ),
        )
    )

    home_market_probability = None
    draw_market_probability = None
    away_market_probability = None

    home_dispersion = None
    draw_dispersion = None
    away_dispersion = None

    home_movement = None
    draw_movement = None
    away_movement = None

    if market:

        selections = (
            market[
                "selections"
            ]
        )

        home = (
            selections[
                "HOME"
            ]
        )

        draw = (
            selections[
                "DRAW"
            ]
        )

        away = (
            selections[
                "AWAY"
            ]
        )

        home_market_probability = (
            home[
                "consensus_probability"
            ]
        )

        draw_market_probability = (
            draw[
                "consensus_probability"
            ]
        )

        away_market_probability = (
            away[
                "consensus_probability"
            ]
        )

        home_dispersion = (
            home[
                "odds_dispersion"
            ]
        )

        draw_dispersion = (
            draw[
                "odds_dispersion"
            ]
        )

        away_dispersion = (
            away[
                "odds_dispersion"
            ]
        )

        home_movement = (
            home[
                "odds_change_pct"
            ]
        )

        draw_movement = (
            draw[
                "odds_change_pct"
            ]
        )

        away_movement = (
            away[
                "odds_change_pct"
            ]
        )

    # ========================================================
    # RETURN
    # ========================================================

    return {

        # POWER

        "home_elo":
            round(
                float(
                    home_elo
                ),
                4,
            ),

        "away_elo":
            round(
                float(
                    away_elo
                ),
                4,
            ),

        "elo_difference":
            round(
                float(
                    home_elo
                    - away_elo
                ),
                4,
            ),


        # FORM

        "home_weighted_form":
            home_form[
                "weighted_form"
            ],

        "away_weighted_form":
            away_form[
                "weighted_form"
            ],

        "home_opponent_strength":
            home_form[
                "opponent_strength"
            ],

        "away_opponent_strength":
            away_form[
                "opponent_strength"
            ],

        "home_strength_adjusted_form":
            home_form[
                "strength_adjusted_form"
            ],

        "away_strength_adjusted_form":
            away_form[
                "strength_adjusted_form"
            ],


        # COVERAGE

        "home_history_count":
            home_form[
                "matches"
            ],

        "away_history_count":
            away_form[
                "matches"
            ],


        # MARKET

        "home_market_probability":
            home_market_probability,

        "draw_market_probability":
            draw_market_probability,

        "away_market_probability":
            away_market_probability,

        "home_market_dispersion":
            home_dispersion,

        "draw_market_dispersion":
            draw_dispersion,

        "away_market_dispersion":
            away_dispersion,

        "home_odds_movement":
            home_movement,

        "draw_odds_movement":
            draw_movement,

        "away_odds_movement":
            away_movement,
    }