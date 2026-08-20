from __future__ import annotations

from collections import defaultdict

from statistics import (
    mean,
    median,
    pstdev,
)

from sqlalchemy.orm import Session

from app.models.market import Market
from app.models.market_odds import (
    MarketOdds,
)


MARKET_SELECTIONS = {
    "1X2": [
        "HOME",
        "DRAW",
        "AWAY",
    ],

    "DC": [
        "1X",
        "X2",
        "12",
    ],

    "OU_25": [
        "OVER",
        "UNDER",
    ],

    "BTTS": [
        "YES",
        "NO",
    ],
}


def get_market(
    db: Session,
    *,
    sport: str,
    code: str,
):

    return (
        db.query(Market)
        .filter(
            Market.sport
            == sport,

            Market.code
            == code,
        )
        .first()
    )


def latest_quotes_per_bookmaker(
    db: Session,
    *,
    match_id: int,
    market_id: int,
    selection: str,
    before_time,
):

    rows = (
        db.query(
            MarketOdds
        )
        .filter(
            MarketOdds.match_id
            == match_id,

            MarketOdds.market_id
            == market_id,

            MarketOdds.selection
            == selection,

            MarketOdds.recorded_at
            <= before_time,
        )
        .order_by(
            MarketOdds.recorded_at.desc(),
            MarketOdds.id.desc(),
        )
        .all()
    )

    result = {}

    for row in rows:

        bookmaker = (
            row.bookmaker
            or "UNKNOWN"
        )

        if bookmaker not in result:

            result[
                bookmaker
            ] = row

    return result


def opening_quotes_per_bookmaker(
    db: Session,
    *,
    match_id: int,
    market_id: int,
    selection: str,
    before_time,
):

    rows = (
        db.query(
            MarketOdds
        )
        .filter(
            MarketOdds.match_id
            == match_id,

            MarketOdds.market_id
            == market_id,

            MarketOdds.selection
            == selection,

            MarketOdds.recorded_at
            <= before_time,
        )
        .order_by(
            MarketOdds.recorded_at.asc(),
            MarketOdds.id.asc(),
        )
        .all()
    )

    result = {}

    for row in rows:

        bookmaker = (
            row.bookmaker
            or "UNKNOWN"
        )

        if bookmaker not in result:

            result[
                bookmaker
            ] = row

    return result


def calculate_selection_consensus(
    db: Session,
    *,
    match_id: int,
    market_id: int,
    selection: str,
    snapshot_at,
):

    latest = (
        latest_quotes_per_bookmaker(
            db=db,
            match_id=match_id,
            market_id=market_id,
            selection=selection,
            before_time=snapshot_at,
        )
    )

    if not latest:
        return None

    current_odds = [
        float(
            row.odds
        )
        for row in latest.values()
        if row.odds
        and float(row.odds) > 1.0
    ]

    if not current_odds:
        return None

    opening = (
        opening_quotes_per_bookmaker(
            db=db,
            match_id=match_id,
            market_id=market_id,
            selection=selection,
            before_time=snapshot_at,
        )
    )

    opening_odds = [
        float(
            row.odds
        )
        for row in opening.values()
        if row.odds
        and float(row.odds) > 1.0
    ]

    median_current = (
        median(
            current_odds
        )
    )

    median_opening = (
        median(
            opening_odds
        )
        if opening_odds
        else None
    )

    implied = (
        100.0
        / median_current
    )

    dispersion = (
        pstdev(
            current_odds
        )
        if len(current_odds) > 1
        else 0.0
    )

    movement = None

    if (
        median_opening
        and median_opening > 0
    ):

        movement = (
            (
                median_current
                - median_opening
            )
            / median_opening
            * 100.0
        )

    return {
        "bookmaker_count":
            len(
                current_odds
            ),

        "best_odds":
            max(
                current_odds
            ),

        "median_odds":
            median_current,

        "mean_odds":
            mean(
                current_odds
            ),

        "min_odds":
            min(
                current_odds
            ),

        "max_odds":
            max(
                current_odds
            ),

        "raw_implied_probability":
            implied,

        "odds_dispersion":
            dispersion,

        "opening_odds":
            median_opening,

        "current_odds":
            median_current,

        "odds_change_pct":
            movement,
    }


def calculate_full_market_consensus(
    db: Session,
    *,
    match_id: int,
    market_code: str,
    snapshot_at,
    sport: str = "football",
):

    market = (
        get_market(
            db=db,
            sport=sport,
            code=market_code,
        )
    )

    if market is None:
        return None

    selections = (
        MARKET_SELECTIONS.get(
            market_code
        )
    )

    if not selections:
        return None

    result = {}

    for selection in selections:

        consensus = (
            calculate_selection_consensus(
                db=db,
                match_id=match_id,
                market_id=market.id,
                selection=selection,
                snapshot_at=snapshot_at,
            )
        )

        if consensus:

            result[
                selection
            ] = consensus

    if (
        len(result)
        != len(selections)
    ):
        return None

    implied_total = sum(
        item[
            "raw_implied_probability"
        ]
        for item in result.values()
    )

    if implied_total <= 0:
        return None

    for selection in selections:

        result[
            selection
        ][
            "consensus_probability"
        ] = (
            result[
                selection
            ][
                "raw_implied_probability"
            ]
            /
            implied_total
            * 100.0
        )

    return {
        "market":
            market,

        "selections":
            result,

        "overround":
            implied_total,
    }