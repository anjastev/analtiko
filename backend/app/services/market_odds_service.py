from __future__ import annotations

from datetime import (
    datetime,
    timedelta,
    timezone,
)

from sqlalchemy import (
    and_,
    func,
)

from sqlalchemy.orm import Session

from app.models.market import Market
from app.models.market_odds import MarketOdds


DEFAULT_MAX_AGE_HOURS = 12


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


def get_market(
    db: Session,
    sport: str,
    market_code: str,
):

    return (
        db.query(Market)
        .filter(
            Market.sport == sport,
            Market.code == market_code,
        )
        .first()
    )


def get_latest_market_odds(
    db: Session,
    *,
    match_id: int,
    market_code: str,
    selection: str,
    sport: str = "football",
    bookmaker: str | None = None,
):

    market = (
        get_market(
            db=db,
            sport=sport,
            market_code=market_code,
        )
    )

    if market is None:
        return None

    query = (
        db.query(MarketOdds)
        .filter(
            MarketOdds.match_id
            == match_id,

            MarketOdds.market_id
            == market.id,

            MarketOdds.selection
            == selection,
        )
    )

    if bookmaker is not None:

        query = query.filter(
            MarketOdds.bookmaker
            == bookmaker
        )

    return (
        query
        .order_by(
            MarketOdds.recorded_at.desc(),
            MarketOdds.id.desc(),
        )
        .first()
    )


def get_latest_odds_per_bookmaker(
    db: Session,
    *,
    match_id: int,
    market_code: str,
    selection: str,
    sport: str = "football",
):

    market = (
        get_market(
            db=db,
            sport=sport,
            market_code=market_code,
        )
    )

    if market is None:
        return []

    subquery = (
        db.query(
            MarketOdds.bookmaker.label(
                "bookmaker"
            ),
            func.max(
                MarketOdds.recorded_at
            ).label(
                "latest_recorded_at"
            ),
        )
        .filter(
            MarketOdds.match_id
            == match_id,

            MarketOdds.market_id
            == market.id,

            MarketOdds.selection
            == selection,
        )
        .group_by(
            MarketOdds.bookmaker
        )
        .subquery()
    )

    rows = (
        db.query(MarketOdds)
        .join(
            subquery,
            and_(
                MarketOdds.bookmaker
                == subquery.c.bookmaker,

                MarketOdds.recorded_at
                == subquery.c.latest_recorded_at,
            ),
        )
        .filter(
            MarketOdds.match_id
            == match_id,

            MarketOdds.market_id
            == market.id,

            MarketOdds.selection
            == selection,
        )
        .order_by(
            MarketOdds.odds.desc(),
            MarketOdds.id.desc(),
        )
        .all()
    )

    # Defensive dedupe if the same bookmaker has multiple
    # records with identical timestamps.
    seen = set()
    result = []

    for row in rows:

        bookmaker = (
            row.bookmaker
            or "UNKNOWN"
        )

        if bookmaker in seen:
            continue

        seen.add(
            bookmaker
        )

        result.append(
            row
        )

    return result


def is_odds_fresh(
    odds_row: MarketOdds,
    *,
    reference_time: datetime | None = None,
    max_age_hours: int = DEFAULT_MAX_AGE_HOURS,
) -> bool:

    if odds_row is None:
        return False

    recorded_at = (
        ensure_utc(
            odds_row.recorded_at
        )
    )

    if recorded_at is None:
        return False

    if reference_time is None:

        reference_time = (
            datetime.now(
                timezone.utc
            )
        )

    reference_time = (
        ensure_utc(
            reference_time
        )
    )

    cutoff = (
        reference_time
        - timedelta(
            hours=max_age_hours
        )
    )

    return (
        recorded_at
        >= cutoff
        and
        recorded_at
        <= reference_time
        + timedelta(
            minutes=10
        )
    )


def get_best_market_odds(
    db: Session,
    *,
    match_id: int,
    market_code: str,
    selection: str,
    sport: str = "football",
    reference_time: datetime | None = None,
    max_age_hours: int = DEFAULT_MAX_AGE_HOURS,
):

    rows = (
        get_latest_odds_per_bookmaker(
            db=db,
            match_id=match_id,
            market_code=market_code,
            selection=selection,
            sport=sport,
        )
    )

    fresh_rows = [
        row
        for row in rows
        if is_odds_fresh(
            row,
            reference_time=reference_time,
            max_age_hours=max_age_hours,
        )
    ]

    if not fresh_rows:
        return None

    return max(
        fresh_rows,
        key=lambda row:
            float(
                row.odds
            ),
    )


def decimal_odds_to_probability(
    odds: float | None,
) -> float | None:

    if (
        odds is None
        or odds <= 1.0
    ):
        return None

    return (
        100.0
        / float(
            odds
        )
    )


def probability_to_fair_odds(
    probability: float | None,
) -> float | None:

    if (
        probability is None
        or probability <= 0
    ):
        return None

    return (
        100.0
        / float(
            probability
        )
    )


def calculate_two_way_no_vig(
    odds_a: float,
    odds_b: float,
):

    if (
        odds_a <= 1.0
        or odds_b <= 1.0
    ):
        return None

    raw_a = (
        1.0
        / odds_a
    )

    raw_b = (
        1.0
        / odds_b
    )

    total = (
        raw_a
        + raw_b
    )

    if total <= 0:
        return None

    return {
        "A":
            raw_a
            / total
            * 100.0,

        "B":
            raw_b
            / total
            * 100.0,

        "overround":
            total
            * 100.0,
    }


def calculate_three_way_no_vig(
    home_odds: float,
    draw_odds: float,
    away_odds: float,
):

    if (
        home_odds <= 1.0
        or draw_odds <= 1.0
        or away_odds <= 1.0
    ):
        return None

    raw_home = (
        1.0
        / home_odds
    )

    raw_draw = (
        1.0
        / draw_odds
    )

    raw_away = (
        1.0
        / away_odds
    )

    total = (
        raw_home
        + raw_draw
        + raw_away
    )

    if total <= 0:
        return None

    return {
        "HOME":
            raw_home
            / total
            * 100.0,

        "DRAW":
            raw_draw
            / total
            * 100.0,

        "AWAY":
            raw_away
            / total
            * 100.0,

        "overround":
            total
            * 100.0,
    }