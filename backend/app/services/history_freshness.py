from datetime import (
    datetime,
    timedelta,
    timezone,
)

from sqlalchemy.orm import Session

from app.models.history_sync_state import (
    HistorySyncState,
)
from app.models.team_match_history import (
    TeamMatchHistory,
)


MIN_GENERAL_HISTORY = 5
MIN_VENUE_HISTORY = 5
FRESH_DAYS = 45

SYNC_COOLDOWN_HOURS = 12


def ensure_utc(
    value: datetime | None,
):

    if value is None:
        return None

    if value.tzinfo is None:

        return value.replace(
            tzinfo=timezone.utc
        )

    return value.astimezone(
        timezone.utc
    )


def get_latest_history(
    db: Session,
    team_id: int,
):

    return (
        db.query(
            TeamMatchHistory
        )
        .filter(
            TeamMatchHistory.team_id
            == team_id
        )
        .order_by(
            TeamMatchHistory.match_date
            .desc()
        )
        .first()
    )


def get_general_count(
    db: Session,
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
        .count()
    )


def get_venue_count(
    db: Session,
    team_id: int,
    before_date,
    venue: str,
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

            TeamMatchHistory.venue
            == venue,
        )
        .count()
    )


def is_history_fresh(
    latest_history_at,
    before_date,
):

    if latest_history_at is None:
        return False

    latest_history_at = (
        ensure_utc(
            latest_history_at
        )
    )

    before_date = (
        ensure_utc(
            before_date
        )
    )

    cutoff = (
        before_date
        - timedelta(
            days=FRESH_DAYS
        )
    )

    return (
        latest_history_at
        >= cutoff
    )


def team_data_ready(
    db: Session,
    team_id: int,
    before_date,
    venue: str,
):

    general_count = (
        get_general_count(
            db=db,
            team_id=team_id,
            before_date=before_date,
        )
    )

    venue_count = (
        get_venue_count(
            db=db,
            team_id=team_id,
            before_date=before_date,
            venue=venue,
        )
    )

    latest = (
        get_latest_history(
            db=db,
            team_id=team_id,
        )
    )

    latest_at = (
        latest.match_date
        if latest
        else None
    )

    fresh = (
        is_history_fresh(
            latest_history_at=latest_at,
            before_date=before_date,
        )
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
            (
                general_count
                >= MIN_GENERAL_HISTORY
                and
                venue_count
                >= MIN_VENUE_HISTORY
                and
                fresh
            ),
    }


def should_sync_team(
    db: Session,
    team_id: int,
    now,
):

    state = (
        db.query(
            HistorySyncState
        )
        .filter(
            HistorySyncState.team_id
            == team_id
        )
        .first()
    )

    if state is None:
        return True

    if (
        state.last_success_at
        is None
    ):
        return True

    now = (
        ensure_utc(
            now
        )
    )

    last_success_at = (
        ensure_utc(
            state.last_success_at
        )
    )

    cutoff = (
        now
        - timedelta(
            hours=SYNC_COOLDOWN_HOURS
        )
    )

    return (
        last_success_at
        < cutoff
    )