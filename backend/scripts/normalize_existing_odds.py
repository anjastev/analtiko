from app.database.database import (
    Base,
    SessionLocal,
    engine,
)

from app.models.market import Market
from app.models.market_odds import MarketOdds
from app.models.odds import Odds

import app.models


# ============================================================
# CONFIG
# ============================================================

SPORT = "football"


# ============================================================
# HELPERS
# ============================================================

def get_market(
    db,
    code: str,
):
    return (
        db.query(Market)
        .filter(
            Market.sport == SPORT,
            Market.code == code,
        )
        .first()
    )


def market_odds_exists(
    db,
    match_id: int,
    market_id: int,
    selection: str,
    bookmaker: str | None,
    odds_value: float,
    recorded_at,
) -> bool:

    existing = (
        db.query(MarketOdds)
        .filter(
            MarketOdds.match_id == match_id,
            MarketOdds.market_id == market_id,
            MarketOdds.selection == selection,
            MarketOdds.bookmaker == bookmaker,
            MarketOdds.odds == odds_value,
            MarketOdds.recorded_at == recorded_at,
        )
        .first()
    )

    return existing is not None


def save_market_odds(
    db,
    source_odds: Odds,
    market: Market,
    selection: str,
    odds_value: float | None,
):
    """
    Normalize one legacy Odds field into the generic
    market_odds table.
    """

    if odds_value is None:
        return "missing"

    try:
        odds_value = float(
            odds_value
        )
    except (TypeError, ValueError):
        return "invalid"

    if odds_value <= 1.0:
        return "invalid"

    if market_odds_exists(
        db=db,
        match_id=source_odds.match_id,
        market_id=market.id,
        selection=selection,
        bookmaker=source_odds.bookmaker,
        odds_value=odds_value,
        recorded_at=source_odds.recorded_at,
    ):
        return "unchanged"

    row = MarketOdds(
        match_id=source_odds.match_id,
        market_id=market.id,
        selection=selection,
        bookmaker=source_odds.bookmaker,
        odds=odds_value,
        source="legacy_odds",
        recorded_at=source_odds.recorded_at,
    )

    db.add(
        row
    )

    return "created"


# ============================================================
# MAIN
# ============================================================

def run():

    Base.metadata.create_all(
        bind=engine
    )

    db = SessionLocal()

    source_rows = 0
    opportunities = 0
    created = 0
    unchanged = 0
    missing = 0
    invalid = 0

    try:

        # ====================================================
        # REQUIRED MARKETS
        # ====================================================

        market_1x2 = (
            get_market(
                db,
                "1X2",
            )
        )

        market_ou25 = (
            get_market(
                db,
                "OU_25",
            )
        )

        market_btts = (
            get_market(
                db,
                "BTTS",
            )
        )

        missing_markets = []

        if market_1x2 is None:
            missing_markets.append(
                "1X2"
            )

        if market_ou25 is None:
            missing_markets.append(
                "OU_25"
            )

        if market_btts is None:
            missing_markets.append(
                "BTTS"
            )

        if missing_markets:

            raise RuntimeError(
                "Missing markets: "
                + ", ".join(
                    missing_markets
                )
                + ". Run scripts.add_football_markets first."
            )

        # ====================================================
        # LEGACY ODDS
        # ====================================================

        odds_rows = (
            db.query(Odds)
            .order_by(
                Odds.recorded_at.asc(),
                Odds.id.asc(),
            )
            .all()
        )

        print()
        print("=" * 80)
        print(
            "ANALITIKO LEGACY ODDS NORMALIZATION"
        )
        print("=" * 80)

        print(
            f"Legacy odds rows: "
            f"{len(odds_rows)}"
        )

        # ====================================================
        # PROCESS
        # ====================================================

        for source_odds in odds_rows:

            source_rows += 1

            mappings = [
                (
                    market_1x2,
                    "HOME",
                    source_odds.home_win,
                ),
                (
                    market_1x2,
                    "DRAW",
                    source_odds.draw,
                ),
                (
                    market_1x2,
                    "AWAY",
                    source_odds.away_win,
                ),
                (
                    market_ou25,
                    "OVER",
                    source_odds.over_25,
                ),
                (
                    market_ou25,
                    "UNDER",
                    source_odds.under_25,
                ),
                (
                    market_btts,
                    "YES",
                    source_odds.btts_yes,
                ),
                (
                    market_btts,
                    "NO",
                    source_odds.btts_no,
                ),
            ]

            for (
                market,
                selection,
                odds_value,
            ) in mappings:

                opportunities += 1

                status = (
                    save_market_odds(
                        db=db,
                        source_odds=source_odds,
                        market=market,
                        selection=selection,
                        odds_value=odds_value,
                    )
                )

                if status == "created":
                    created += 1

                elif status == "unchanged":
                    unchanged += 1

                elif status == "missing":
                    missing += 1

                elif status == "invalid":
                    invalid += 1

        # ====================================================
        # COMMIT
        # ====================================================

        db.commit()

        # ====================================================
        # FINAL COUNTS
        # ====================================================

        total_market_odds = (
            db.query(MarketOdds)
            .count()
        )

        print()
        print("=" * 80)
        print(
            "NORMALIZATION SUMMARY"
        )
        print("=" * 80)

        print(
            f"Legacy rows processed:    "
            f"{source_rows}"
        )

        print(
            f"Field opportunities:      "
            f"{opportunities}"
        )

        print(
            f"Market odds created:      "
            f"{created}"
        )

        print(
            f"Market odds unchanged:    "
            f"{unchanged}"
        )

        print(
            f"Missing values:           "
            f"{missing}"
        )

        print(
            f"Invalid values:           "
            f"{invalid}"
        )

        print(
            f"Total market_odds rows:   "
            f"{total_market_odds}"
        )

        print()

        if source_rows == 0:

            print(
                "STATUS: PARTIAL "
                "(no legacy odds found)"
            )

        elif created == 0 and unchanged == 0:

            print(
                "STATUS: PARTIAL "
                "(no usable odds found)"
            )

        else:

            print(
                "STATUS: OK"
            )

        print("=" * 80)

    except Exception:

        db.rollback()
        raise

    finally:

        db.close()


if __name__ == "__main__":
    run()