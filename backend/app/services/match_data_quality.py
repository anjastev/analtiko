from __future__ import annotations

from datetime import (
    datetime,
    timedelta,
    timezone,
)

from sqlalchemy.orm import Session

from app.models.match import Match
from app.models.team_match_history import (
    TeamMatchHistory,
)


STATUS_READY = "READY"
STATUS_PARTIAL = "PARTIAL"
STATUS_BLOCKED = "BLOCKED"


MIN_GENERAL_HISTORY = 5
MIN_VENUE_HISTORY = 5
FRESH_DAYS = 45


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


def get_team_history_state(
    db: Session,
    *,
    team_id: int,
    before_date,
    venue: str,
) -> dict:

    before_utc = ensure_utc(
        before_date
    )

    general_query = (
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

    general_count = (
        general_query.count()
    )

    venue_count = (
        general_query
        .filter(
            TeamMatchHistory.venue
            == venue
        )
        .count()
    )

    latest = (
        general_query
        .order_by(
            TeamMatchHistory.match_date
            .desc()
        )
        .first()
    )

    latest_at = (
        latest.match_date
        if latest
        else None
    )

    latest_utc = (
        ensure_utc(
            latest_at
        )
    )

    freshness_cutoff = (
        before_utc
        - timedelta(
            days=FRESH_DAYS
        )
    )

    fresh = (
        latest_utc is not None
        and
        latest_utc
        >= freshness_cutoff
    )

    ready = (
        general_count
        >= MIN_GENERAL_HISTORY
        and
        venue_count
        >= MIN_VENUE_HISTORY
        and
        fresh
    )

    return {
        "general_count":
            general_count,

        "venue_count":
            venue_count,

        "latest_history_at":
            latest_at,

        "fresh":
            fresh,

        "ready":
            ready,
    }


def evaluate_match_data_quality(
    db: Session,
    match: Match,
) -> dict:

    home = (
        get_team_history_state(
            db=db,
            team_id=(
                match.home_team_id
            ),
            before_date=(
                match.match_date
            ),
            venue="home",
        )
    )

    away = (
        get_team_history_state(
            db=db,
            team_id=(
                match.away_team_id
            ),
            before_date=(
                match.match_date
            ),
            venue="away",
        )
    )

    if (
        home["ready"]
        and
        away["ready"]
    ):

        status = STATUS_READY

    elif (
        home["general_count"] > 0
        or
        away["general_count"] > 0
    ):

        status = STATUS_PARTIAL

    else:

        status = STATUS_BLOCKED

    return {
        "match_id":
            match.id,

        "status":
            status,

        "ready":
            (
                status
                == STATUS_READY
            ),

        "home":
            home,

        "away":
            away,
    }


def is_match_production_ready(
    db: Session,
    match: Match,
) -> bool:

    return bool(
        evaluate_match_data_quality(
            db=db,
            match=match,
        )[
            "ready"
        ]
    )