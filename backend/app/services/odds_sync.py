from datetime import datetime

from sqlalchemy.orm import Session

from app.collectors.api_football import APIFootballClient
from app.models.match import Match
from app.models.odds import Odds
from app.services.odds_parser import parse_odds_response


def odds_are_equal(
    old_value: float | None,
    new_value: float | None,
) -> bool:
    """
    Compare two odds values.

    None == None -> same
    None != number -> changed
    Numbers are compared with small tolerance.
    """

    if old_value is None and new_value is None:
        return True

    if old_value is None or new_value is None:
        return False

    return abs(old_value - new_value) < 0.001


def odds_have_changed(
    latest: Odds,
    parsed: dict,
) -> bool:
    """
    Return True if at least one market changed.
    """

    comparisons = [
        odds_are_equal(
            latest.home_win,
            parsed["home_win"],
        ),
        odds_are_equal(
            latest.draw,
            parsed["draw"],
        ),
        odds_are_equal(
            latest.away_win,
            parsed["away_win"],
        ),
        odds_are_equal(
            latest.over_25,
            parsed["over_25"],
        ),
        odds_are_equal(
            latest.under_25,
            parsed["under_25"],
        ),
        odds_are_equal(
            latest.btts_yes,
            parsed["btts_yes"],
        ),
        odds_are_equal(
            latest.btts_no,
            parsed["btts_no"],
        ),
    ]

    return not all(comparisons)


def sync_odds_for_match(
    db: Session,
    client: APIFootballClient,
    match: Match,
) -> tuple[Odds | None, str]:

    if not match.external_id:
        return None, "no_external_id"

    # 1. Get current odds from API
    data = client.get_odds_by_fixture(
        match.external_id
    )

    # 2. Parse API response
    parsed = parse_odds_response(data)

    if not parsed:
        return None, "no_odds"

    # We require 1/X/2
    if (
        parsed["home_win"] is None
        or parsed["draw"] is None
        or parsed["away_win"] is None
    ):
        return None, "incomplete_odds"

    # 3. Find latest stored snapshot
    latest = (
        db.query(Odds)
        .filter(
            Odds.match_id == match.id
        )
        .order_by(
            Odds.recorded_at.desc()
        )
        .first()
    )

    # 4. If we already have odds, compare them
    if latest:
        same_bookmaker = (
            (latest.bookmaker or "").lower()
            == (parsed["bookmaker"] or "").lower()
        )

        changed = odds_have_changed(
            latest,
            parsed,
        )

        if same_bookmaker and not changed:
            return latest, "unchanged"

    # 5. Save new snapshot
    snapshot = Odds(
        match_id=match.id,

        bookmaker=parsed["bookmaker"],

        home_win=parsed["home_win"],
        draw=parsed["draw"],
        away_win=parsed["away_win"],

        over_25=parsed["over_25"],
        under_25=parsed["under_25"],

        btts_yes=parsed["btts_yes"],
        btts_no=parsed["btts_no"],

        recorded_at=datetime.utcnow(),
    )

    db.add(snapshot)
    db.flush()

    return snapshot, "saved"