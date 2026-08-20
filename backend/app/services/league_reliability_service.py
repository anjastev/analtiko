from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.league import League
from app.models.match import Match
from app.models.signal import Signal


PRIOR_RELIABILITY = 0.70

FULL_CONFIDENCE_SAMPLE = 50


def calculate_league_stats(
    db: Session,
    league: League,
):

    rows = (
        db.query(Signal)
        .join(
            Match,
            Match.id
            == Signal.match_id,
        )
        .filter(
            Match.league_id
            == league.id,

            Signal.is_value
            .is_(True),

            Signal.evaluated_at
            .isnot(None),

            Signal.correct
            .isnot(None),
        )
        .all()
    )

    n = len(rows)

    wins = sum(
        1
        for row in rows
        if row.correct is True
    )

    losses = sum(
        1
        for row in rows
        if row.correct is False
    )

    hit_rate = (
        wins
        / n
        if n
        else None
    )

    average_edge = (
        sum(
            float(
                row.edge
                or 0.0
            )
            for row in rows
        )
        / n
        if n
        else None
    )

    roi = (
        sum(
            float(
                row.profit
                or 0.0
            )
            for row in rows
        )
        / n
        if n
        else None
    )

    sample_confidence = min(
        n
        / FULL_CONFIDENCE_SAMPLE,
        1.0,
    )

    if hit_rate is None:

        observed = (
            PRIOR_RELIABILITY
        )

    else:

        # Map hit rate conservatively
        # into reliability range.

        observed = (
            0.40
            +
            hit_rate
            * 0.60
        )

    reliability = (
        PRIOR_RELIABILITY
        * (
            1.0
            - sample_confidence
        )
        +
        observed
        * sample_confidence
    )

    reliability = max(
        0.40,
        min(
            1.00,
            reliability,
        ),
    )

    return {
        "evaluated_signals":
            n,

        "wins":
            wins,

        "losses":
            losses,

        "hit_rate":
            (
                hit_rate
                * 100.0
                if hit_rate
                is not None
                else None
            ),

        "average_edge":
            average_edge,

        "roi":
            (
                roi
                * 100.0
                if roi
                is not None
                else None
            ),

        "reliability_score":
            reliability,

        "sample_confidence":
            sample_confidence,
    }