from __future__ import annotations

from datetime import (
    datetime,
    timezone,
)

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.combination import Combination
from app.models.market_odds import MarketOdds
from app.models.match import Match
from app.models.signal import Signal

from app.services.match_data_quality import (
    evaluate_match_data_quality,
)

from app.services.market_odds_service import (
    is_odds_fresh,
)


FINISHED_STATUSES = {
    "FT",
    "AET",
    "PEN",
}


def get_backend_health(
    db: Session,
) -> dict:

    now = datetime.now(
        timezone.utc
    )

    upcoming_matches = (
        db.query(Match)
        .filter(
            Match.match_date >= now,
            ~Match.status.in_(
                FINISHED_STATUSES
            ),
        )
        .all()
    )

    ready_matches = 0

    for match in upcoming_matches:

        quality = (
            evaluate_match_data_quality(
                db=db,
                match=match,
            )
        )

        if quality["ready"]:
            ready_matches += 1

    active_signals = (
        db.query(Signal)
        .join(
            Match,
            Match.id
            == Signal.match_id,
        )
        .filter(
            Signal.active.is_(True),
            Match.match_date >= now,
        )
        .count()
    )

    value_signals = (
        db.query(Signal)
        .join(
            Match,
            Match.id
            == Signal.match_id,
        )
        .filter(
            Signal.active.is_(True),
            Signal.is_value.is_(True),
            Match.match_date >= now,
        )
        .count()
    )

    pending_combinations = (
        db.query(Combination)
        .filter(
            Combination.status
            == "pending"
        )
        .count()
    )

    odds_rows = (
        db.query(MarketOdds)
        .all()
    )

    fresh_odds_rows = sum(
        1
        for row in odds_rows
        if is_odds_fresh(
            row,
            reference_time=now,
            max_age_hours=12,
        )
    )

    total_matches = len(
        upcoming_matches
    )

    production_coverage = (
        ready_matches
        / total_matches
        * 100.0
        if total_matches
        else 0.0
    )

    if (
        total_matches > 0
        and production_coverage >= 70.0
        and fresh_odds_rows > 0
    ):
        status = "OK"

    elif total_matches == 0:
        status = "NO_UPCOMING_MATCHES"

    else:
        status = "PARTIAL"

    return {
        "status":
            status,

        "timestamp":
            now.isoformat(),

        "upcoming_matches":
            total_matches,

        "production_ready_matches":
            ready_matches,

        "production_coverage":
            round(
                production_coverage,
                2,
            ),

        "active_signals":
            active_signals,

        "value_signals":
            value_signals,

        "pending_combinations":
            pending_combinations,

        "fresh_odds_rows":
            fresh_odds_rows,
    }