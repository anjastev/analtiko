from __future__ import annotations

from datetime import timedelta

from sqlalchemy.orm import Session

from app.models.market_odds import MarketOdds
from app.models.signal import Signal


CLOSING_WINDOW_MINUTES = 90


def find_closing_odds(
    db: Session,
    *,
    signal: Signal,
    kickoff,
):

    if signal.bookmaker is None:
        return None

    start = (
        kickoff
        - timedelta(
            minutes=CLOSING_WINDOW_MINUTES
        )
    )

    row = (
        db.query(
            MarketOdds
        )
        .filter(
            MarketOdds.match_id
            == signal.match_id,

            MarketOdds.market_id
            == signal.market_id,

            MarketOdds.selection
            == signal.selection,

            MarketOdds.bookmaker
            == signal.bookmaker,

            MarketOdds.recorded_at
            >= start,

            MarketOdds.recorded_at
            < kickoff,
        )
        .order_by(
            MarketOdds.recorded_at
            .desc(),

            MarketOdds.id
            .desc(),
        )
        .first()
    )

    return row


def calculate_clv(
    recommended_odds: float,
    closing_odds: float,
):

    if (
        recommended_odds <= 1.0
        or closing_odds <= 1.0
    ):
        return None

    # Positive when our recommended
    # price was better than closing price.

    return (
        (
            recommended_odds
            / closing_odds
        )
        - 1.0
    ) * 100.0