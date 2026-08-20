from datetime import (
    datetime,
    timezone,
)

from app.database.database import (
    SessionLocal,
)

from app.models.market import Market
from app.models.match import Match
from app.models.signal import Signal

from app.services.direct_market_value import (
    find_best_value_quote,
)

from app.services.match_data_quality import (
    is_match_production_ready,
)


SPORT = "football"

PRODUCTION_MARKETS = {
    "DC",
}


MIN_VALUE_EDGE = 5.0
MIN_EXPECTED_VALUE = 0.0


def clear_value(
    signal,
):

    signal.odds = None
    signal.bookmaker = None
    signal.odds_recorded_at = None

    signal.market_probability = None
    signal.edge = None
    signal.expected_value = None

    signal.is_value = False


def run():

    db = SessionLocal()

    now = datetime.now(
        timezone.utc
    )

    processed = 0
    priced = 0

    value_count = 0

    no_direct_odds = 0
    data_blocked = 0

    try:

        markets = (
            db.query(Market)
            .filter(
                Market.sport
                == SPORT,

                Market.code.in_(
                    PRODUCTION_MARKETS
                ),
            )
            .all()
        )

        market_map = {
            market.id:
                market
            for market in markets
        }

        signals = (
            db.query(Signal)
            .join(
                Match,
                Match.id
                == Signal.match_id,
            )
            .filter(
                Signal.active.is_(True),

                Signal.market_id.in_(
                    list(
                        market_map.keys()
                    )
                ),

                Match.match_date
                >= now,
            )
            .all()
        )

        print()
        print("=" * 100)
        print(
            "ANALITIKO PRODUCTION VALUE ENGINE"
        )
        print("=" * 100)

        print(
            f"Signals: "
            f"{len(signals)}"
        )

        for signal in signals:

            processed += 1

            market = (
                market_map[
                    signal.market_id
                ]
            )

            match = (
                db.query(Match)
                .filter(
                    Match.id
                    == signal.match_id
                )
                .first()
            )

            if match is None:

                clear_value(
                    signal
                )

                continue

            if not (
                is_match_production_ready(
                    db=db,
                    match=match,
                )
            ):

                data_blocked += 1

                clear_value(
                    signal
                )

                continue

            quote = (
                find_best_value_quote(
                    db=db,

                    match_id=(
                        signal.match_id
                    ),

                    market_code=(
                        market.code
                    ),

                    selection=(
                        signal.selection
                    ),

                    model_probability=(
                        float(
                            signal.model_probability
                        )
                    ),

                    sport=SPORT,

                    reference_time=now,

                    max_age_hours=12,
                )
            )

            if quote is None:

                no_direct_odds += 1

                clear_value(
                    signal
                )

                continue

            priced += 1

            odds = float(
                quote[
                    "odds"
                ]
            )

            market_probability = float(
                quote[
                    "market_probability"
                ]
            )

            edge = float(
                quote[
                    "edge"
                ]
            )

            expected_value = float(
                quote[
                    "expected_value"
                ]
            )

            odds_row = (
                quote[
                    "odds_row"
                ]
            )

            is_value = (
                edge
                >= MIN_VALUE_EDGE

                and

                expected_value
                > MIN_EXPECTED_VALUE
            )

            signal.odds = (
                odds
            )

            signal.bookmaker = (
                quote[
                    "bookmaker"
                ]
            )

            signal.odds_recorded_at = (
                odds_row.recorded_at
            )

            signal.market_probability = (
                market_probability
            )

            signal.edge = (
                edge
            )

            signal.expected_value = (
                expected_value
            )

            signal.is_value = (
                is_value
            )

            if is_value:

                value_count += 1

            print()
            print(
                f"{match.home_team.name} "
                f"vs "
                f"{match.away_team.name}"
            )

            print(
                f"  "
                f"{market.code} "
                f"{signal.selection}"
            )

            print(
                f"  Model: "
                f"{signal.model_probability:.1f}%"
            )

            print(
                f"  Market: "
                f"{market_probability:.1f}%"
            )

            print(
                f"  Odds: "
                f"{odds:.2f}"
            )

            print(
                f"  Bookmaker: "
                f"{signal.bookmaker}"
            )

            print(
                f"  Edge: "
                f"{edge:+.2f}%"
            )

            print(
                f"  EV: "
                f"{expected_value:+.2f}%"
            )

            print(
                f"  VALUE: "
                f"{is_value}"
            )

        db.commit()

        print()
        print("=" * 100)
        print(
            "VALUE SUMMARY"
        )
        print("=" * 100)

        print(
            f"Processed: "
            f"{processed}"
        )

        print(
            f"Priced: "
            f"{priced}"
        )

        print(
            f"VALUE: "
            f"{value_count}"
        )

        print(
            f"No odds: "
            f"{no_direct_odds}"
        )

        print(
            f"Data blocked: "
            f"{data_blocked}"
        )

        print(
            "STATUS: OK"
        )

        print("=" * 100)

    except Exception:

        db.rollback()
        raise

    finally:

        db.close()


if __name__ == "__main__":
    run()