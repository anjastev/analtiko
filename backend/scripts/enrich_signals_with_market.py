from datetime import (
    datetime,
    timezone,
)

from app.database.database import (
    Base,
    SessionLocal,
    engine,
)

from app.models.match import Match
from app.models.market import Market
from app.models.odds import Odds
from app.models.signal import Signal

import app.models


# ============================================================
# CONFIG
# ============================================================

SPORT = "football"
MARKET_CODE = "DC"

# Research threshold only.
#
# This is NOT yet a validated profitability threshold.
MIN_VALUE_EDGE = 5.0


# ============================================================
# HELPERS
# ============================================================

def get_double_chance_market(
    db,
):
    return (
        db.query(Market)
        .filter(
            Market.sport == SPORT,
            Market.code == MARKET_CODE,
        )
        .first()
    )


def get_latest_odds(
    db,
    match_id: int,
):
    """
    Return the latest available odds snapshot for the match.
    """

    return (
        db.query(Odds)
        .filter(
            Odds.match_id == match_id
        )
        .order_by(
            Odds.recorded_at.desc(),
            Odds.id.desc(),
        )
        .first()
    )


def calculate_no_vig_1x2(
    home_odds: float,
    draw_odds: float,
    away_odds: float,
):
    """
    Convert bookmaker decimal odds into normalized
    no-vig market probabilities.

    Returns percentages.
    """

    if (
        home_odds is None
        or draw_odds is None
        or away_odds is None
    ):
        return None

    if (
        home_odds <= 1.0
        or draw_odds <= 1.0
        or away_odds <= 1.0
    ):
        return None

    raw_home = (
        1.0 / home_odds
    )

    raw_draw = (
        1.0 / draw_odds
    )

    raw_away = (
        1.0 / away_odds
    )

    total = (
        raw_home
        + raw_draw
        + raw_away
    )

    if total <= 0:
        return None

    home = (
        raw_home
        / total
        * 100.0
    )

    draw = (
        raw_draw
        / total
        * 100.0
    )

    away = (
        raw_away
        / total
        * 100.0
    )

    return {
        "HOME": home,
        "DRAW": draw,
        "AWAY": away,
    }


def get_double_chance_probability(
    selection: str,
    market_probabilities: dict,
):
    """
    Build synthetic Double Chance market probability
    from no-vig 1X2 probabilities.
    """

    home = (
        market_probabilities[
            "HOME"
        ]
    )

    draw = (
        market_probabilities[
            "DRAW"
        ]
    )

    away = (
        market_probabilities[
            "AWAY"
        ]
    )

    if selection == "1X":
        return home + draw

    if selection == "X2":
        return draw + away

    if selection == "12":
        return home + away

    return None


def fair_odds_from_probability(
    probability: float,
):
    """
    Convert percentage probability to fair decimal odds.
    """

    if probability <= 0:
        return None

    return (
        100.0
        / probability
    )


# ============================================================
# MAIN
# ============================================================

def run():

    Base.metadata.create_all(
        bind=engine
    )

    db = SessionLocal()

    now = datetime.now(
        timezone.utc
    )

    total_signals = 0
    enriched = 0

    missing_odds = 0
    invalid_odds = 0

    positive_edge = 0
    value_edge = 0

    try:

        market = (
            get_double_chance_market(
                db
            )
        )

        if market is None:

            raise RuntimeError(
                "Double Chance market missing. "
                "Run scripts.add_football_markets first."
            )

        # ====================================================
        # ACTIVE UPCOMING SIGNALS
        # ====================================================

        signals = (
            db.query(Signal)
            .join(
                Match,
                Match.id
                == Signal.match_id,
            )
            .filter(
                Signal.market_id
                == market.id,

                Signal.active
                .is_(True),

                Match.match_date
                >= now,
            )
            .order_by(
                Match.match_date.asc(),
                Signal.confidence_score.desc(),
            )
            .all()
        )

        print()
        print("=" * 80)
        print(
            "ANALITIKO MARKET SIGNAL ENRICHMENT"
        )
        print("=" * 80)

        print(
            f"Active DC signals: "
            f"{len(signals)}"
        )

        print(
            f"Research value edge: "
            f"{MIN_VALUE_EDGE:.1f}%"
        )

        # ====================================================
        # PROCESS
        # ====================================================

        for signal in signals:

            total_signals += 1

            match = (
                db.query(Match)
                .filter(
                    Match.id
                    == signal.match_id
                )
                .first()
            )

            if match is None:
                continue

            print()
            print("-" * 80)

            print(
                f"[{match.id}] "
                f"{match.home_team.name} "
                f"vs "
                f"{match.away_team.name}"
            )

            print(
                f"Signal: "
                f"{signal.signal_type}"
            )

            print(
                f"Selection: "
                f"{signal.selection}"
            )

            print(
                f"Model probability: "
                f"{signal.model_probability:.1f}%"
            )

            # =================================================
            # ODDS
            # =================================================

            odds = (
                get_latest_odds(
                    db=db,
                    match_id=match.id,
                )
            )

            if odds is None:

                missing_odds += 1

                print(
                    "Market: NO ODDS"
                )

                continue

            market_1x2 = (
                calculate_no_vig_1x2(
                    home_odds=odds.home_win,
                    draw_odds=odds.draw,
                    away_odds=odds.away_win,
                )
            )

            if market_1x2 is None:

                invalid_odds += 1

                print(
                    "Market: INVALID 1X2 ODDS"
                )

                continue

            # =================================================
            # SYNTHETIC DC MARKET
            # =================================================

            market_probability = (
                get_double_chance_probability(
                    selection=signal.selection,
                    market_probabilities=market_1x2,
                )
            )

            if market_probability is None:

                print(
                    "Unsupported selection."
                )

                continue

            edge = (
                signal.model_probability
                - market_probability
            )

            synthetic_fair_odds = (
                fair_odds_from_probability(
                    market_probability
                )
            )

            model_fair_odds = (
                fair_odds_from_probability(
                    signal.model_probability
                )
            )

            # =================================================
            # UPDATE SIGNAL
            # =================================================

            signal.market_probability = round(
                market_probability,
                4,
            )

            signal.edge = round(
                edge,
                4,
            )

            # IMPORTANT:
            #
            # We do NOT populate signal.odds here.
            #
            # The Odds table contains real 1X2 odds,
            # but does not contain direct bookmaker
            # Double Chance prices.
            #
            # Filling signal.odds with synthetic odds would
            # incorrectly make them look like executable
            # bookmaker prices.

            signal.odds = None

            enriched += 1

            if edge > 0:

                positive_edge += 1

            is_value = (
                edge
                >= MIN_VALUE_EDGE
            )

            if is_value:

                value_edge += 1

            print(
                f"Bookmaker: "
                f"{odds.bookmaker or '-'}"
            )

            print(
                "No-vig 1X2: "
                f"H={market_1x2['HOME']:.1f}% "
                f"D={market_1x2['DRAW']:.1f}% "
                f"A={market_1x2['AWAY']:.1f}%"
            )

            print(
                f"Synthetic "
                f"{signal.selection} market: "
                f"{market_probability:.1f}%"
            )

            print(
                f"Edge: "
                f"{edge:+.1f}%"
            )

            print(
                f"Model fair odds: "
                f"{model_fair_odds:.2f}"
            )

            print(
                f"Synthetic market fair odds: "
                f"{synthetic_fair_odds:.2f}"
            )

            if is_value:

                print(
                    "Market status: VALUE"
                )

            elif edge > 0:

                print(
                    "Market status: "
                    "POSITIVE EDGE"
                )

            else:

                print(
                    "Market status: "
                    "NO EDGE"
                )

        # ====================================================
        # COMMIT
        # ====================================================

        db.commit()

        # ====================================================
        # SUMMARY
        # ====================================================

        print()
        print("=" * 80)
        print(
            "MARKET ENRICHMENT SUMMARY"
        )
        print("=" * 80)

        print(
            f"Signals processed:       "
            f"{total_signals}"
        )

        print(
            f"Signals enriched:        "
            f"{enriched}"
        )

        print(
            f"Missing odds:            "
            f"{missing_odds}"
        )

        print(
            f"Invalid odds:            "
            f"{invalid_odds}"
        )

        print(
            f"Positive edge:           "
            f"{positive_edge}"
        )

        print(
            f"VALUE edge >= "
            f"{MIN_VALUE_EDGE:.1f}%:    "
            f"{value_edge}"
        )

        print()

        if total_signals == 0:

            print(
                "STATUS: PARTIAL "
                "(no signals)"
            )

        elif enriched == 0:

            print(
                "STATUS: PARTIAL "
                "(no signals could be enriched)"
            )

        elif missing_odds > 0:

            print(
                "STATUS: PARTIAL "
                "(some signals have no odds)"
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