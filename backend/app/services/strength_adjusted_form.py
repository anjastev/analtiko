from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.team_match_history import (
    TeamMatchHistory,
)

from app.models.team_power_rating import (
    TeamPowerRating,
)

from app.models.match import Match

from app.services.elo_service import (
    DEFAULT_ELO,
)


RECENT_MATCHES = 10

DECAY = 0.88


def result_points(
    result: str,
):

    if result == "W":
        return 1.0

    if result == "D":
        return 0.5

    return 0.0


def get_recent_history(
    db: Session,
    *,
    team_id: int,
    before_date,
):

    return (
        db.query(
            TeamMatchHistory
        )
        .filter(
            TeamMatchHistory.team_id
            == team_id,

            TeamMatchHistory.match_date
            < before_date,
        )
        .order_by(
            TeamMatchHistory.match_date
            .desc()
        )
        .limit(
            RECENT_MATCHES
        )
        .all()
    )


def get_average_recent_opponent_elo(
    db: Session,
    *,
    team_id: int,
    before_date,
):

    rows = (
        db.query(
            TeamPowerRating
        )
        .join(
            Match,
            Match.id
            == TeamPowerRating.match_id,
        )
        .filter(
            TeamPowerRating.team_id
            == team_id,

            Match.match_date
            < before_date,
        )
        .order_by(
            Match.match_date.desc()
        )
        .limit(
            RECENT_MATCHES
        )
        .all()
    )

    if not rows:

        return DEFAULT_ELO

    return (
        sum(
            float(
                row.opponent_rating_before
            )
            for row in rows
        )
        /
        len(rows)
    )


def calculate_strength_adjusted_form(
    db: Session,
    *,
    team_id: int,
    before_date,
):

    history = (
        get_recent_history(
            db=db,
            team_id=team_id,
            before_date=before_date,
        )
    )

    if not history:

        return {
            "matches": 0,
            "weighted_form": 0.0,
            "opponent_strength":
                DEFAULT_ELO,

            "strength_adjusted_form":
                0.0,
        }

    weighted_points = 0.0
    total_weight = 0.0

    for index, match in enumerate(
        history
    ):

        weight = (
            DECAY ** index
        )

        weighted_points += (
            result_points(
                match.result
            )
            * weight
        )

        total_weight += weight

    weighted_form = (
        weighted_points
        / total_weight
        if total_weight
        else 0.0
    )

    opponent_strength = (
        get_average_recent_opponent_elo(
            db=db,
            team_id=team_id,
            before_date=before_date,
        )
    )

    strength_multiplier = (
        opponent_strength
        / DEFAULT_ELO
    )

    adjusted = (
        weighted_form
        * strength_multiplier
    )

    return {
        "matches":
            len(history),

        "weighted_form":
            round(
                weighted_form,
                6,
            ),

        "opponent_strength":
            round(
                opponent_strength,
                4,
            ),

        "strength_adjusted_form":
            round(
                adjusted,
                6,
            ),
    }