from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.match import Match
from app.models.team_power_rating import (
    TeamPowerRating,
)


DEFAULT_ELO = 1500.0

K_FACTOR = 24.0

HOME_ADVANTAGE = 65.0


FINISHED_STATUSES = {
    "FT",
    "AET",
    "PEN",
}


def expected_score(
    rating_a: float,
    rating_b: float,
) -> float:

    return (
        1.0
        /
        (
            1.0
            +
            10.0
            ** (
                (
                    rating_b
                    - rating_a
                )
                / 400.0
            )
        )
    )


def get_actual_scores(
    home_score: int,
    away_score: int,
):

    if home_score > away_score:

        return (
            1.0,
            0.0,
        )

    if home_score < away_score:

        return (
            0.0,
            1.0,
        )

    return (
        0.5,
        0.5,
    )


def calculate_match_ratings(
    *,
    home_rating: float,
    away_rating: float,
    home_score: int,
    away_score: int,
):

    adjusted_home = (
        home_rating
        + HOME_ADVANTAGE
    )

    expected_home = (
        expected_score(
            adjusted_home,
            away_rating,
        )
    )

    expected_away = (
        1.0
        - expected_home
    )

    actual_home, actual_away = (
        get_actual_scores(
            home_score,
            away_score,
        )
    )

    home_change = (
        K_FACTOR
        * (
            actual_home
            - expected_home
        )
    )

    away_change = (
        K_FACTOR
        * (
            actual_away
            - expected_away
        )
    )

    return {
        "home_before":
            home_rating,

        "away_before":
            away_rating,

        "expected_home":
            expected_home,

        "expected_away":
            expected_away,

        "actual_home":
            actual_home,

        "actual_away":
            actual_away,

        "home_change":
            home_change,

        "away_change":
            away_change,

        "home_after":
            home_rating
            + home_change,

        "away_after":
            away_rating
            + away_change,
    }


def rebuild_all_ratings(
    db: Session,
):

    matches = (
        db.query(Match)
        .filter(
            Match.status.in_(
                FINISHED_STATUSES
            ),

            Match.home_score
            .isnot(None),

            Match.away_score
            .isnot(None),
        )
        .order_by(
            Match.match_date.asc(),
            Match.id.asc(),
        )
        .all()
    )

    # Rebuild is intentionally deterministic.
    db.query(
        TeamPowerRating
    ).delete()

    db.flush()

    current_ratings = {}

    rows_created = 0

    for match in matches:

        home_rating = (
            current_ratings.get(
                match.home_team_id,
                DEFAULT_ELO,
            )
        )

        away_rating = (
            current_ratings.get(
                match.away_team_id,
                DEFAULT_ELO,
            )
        )

        result = (
            calculate_match_ratings(
                home_rating=home_rating,
                away_rating=away_rating,
                home_score=(
                    match.home_score
                ),
                away_score=(
                    match.away_score
                ),
            )
        )

        db.add(
            TeamPowerRating(
                team_id=(
                    match.home_team_id
                ),

                match_id=(
                    match.id
                ),

                rating_before=(
                    result[
                        "home_before"
                    ]
                ),

                rating_after=(
                    result[
                        "home_after"
                    ]
                ),

                opponent_rating_before=(
                    result[
                        "away_before"
                    ]
                ),

                expected_score=(
                    result[
                        "expected_home"
                    ]
                ),

                actual_score=(
                    result[
                        "actual_home"
                    ]
                ),

                rating_change=(
                    result[
                        "home_change"
                    ]
                ),
            )
        )

        db.add(
            TeamPowerRating(
                team_id=(
                    match.away_team_id
                ),

                match_id=(
                    match.id
                ),

                rating_before=(
                    result[
                        "away_before"
                    ]
                ),

                rating_after=(
                    result[
                        "away_after"
                    ]
                ),

                opponent_rating_before=(
                    result[
                        "home_before"
                    ]
                ),

                expected_score=(
                    result[
                        "expected_away"
                    ]
                ),

                actual_score=(
                    result[
                        "actual_away"
                    ]
                ),

                rating_change=(
                    result[
                        "away_change"
                    ]
                ),
            )
        )

        current_ratings[
            match.home_team_id
        ] = (
            result[
                "home_after"
            ]
        )

        current_ratings[
            match.away_team_id
        ] = (
            result[
                "away_after"
            ]
        )

        rows_created += 2

    db.commit()

    return {
        "matches":
            len(matches),

        "rows_created":
            rows_created,

        "teams":
            len(
                current_ratings
            ),
    }


def get_team_elo_before(
    db: Session,
    *,
    team_id: int,
    before_date,
) -> float:

    row = (
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
            Match.match_date.desc(),
            TeamPowerRating.id.desc(),
        )
        .first()
    )

    if row is None:
        return DEFAULT_ELO

    return float(
        row.rating_after
    )