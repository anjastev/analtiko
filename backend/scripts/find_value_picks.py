from datetime import (
    datetime,
    timedelta,
)

from sqlalchemy import (
    text,
)

from app.database.database import (
    SessionLocal,
    engine,
)

from app.models.match import (
    Match,
)

from app.models.ml_prediction_snapshot import (
    MLPredictionSnapshot,
)


# ============================================================
# CONFIG
# ============================================================

DAYS_AHEAD = 3

# Research thresholds only.
# These are NOT historically validated betting thresholds.
VALUE_EDGE_THRESHOLD = 5.0

ELITE_VALUE_EDGE_THRESHOLD = 8.0


# ============================================================
# HELPERS
# ============================================================

def normalize_probability(
    value,
):
    """
    Snapshot probabilities may be stored as percentages
    such as 54.6 or as decimals such as 0.546.

    Normalize everything to decimal 0-1.
    """

    if value is None:
        return None

    value = float(
        value
    )

    if value > 1.5:

        return (
            value
            / 100.0
        )

    return value


def normalize_market(
    home_odds,
    draw_odds,
    away_odds,
):
    """
    Convert decimal bookmaker odds to implied probabilities
    and remove bookmaker margin by normalizing the three
    probabilities to sum to 1.
    """

    if (
        home_odds is None
        or draw_odds is None
        or away_odds is None
    ):

        return None


    try:

        home_odds = float(
            home_odds
        )

        draw_odds = float(
            draw_odds
        )

        away_odds = float(
            away_odds
        )

    except (
        TypeError,
        ValueError,
    ):

        return None


    if (
        home_odds <= 1.0
        or draw_odds <= 1.0
        or away_odds <= 1.0
    ):

        return None


    raw = {
        "HOME":
            1.0 / home_odds,

        "DRAW":
            1.0 / draw_odds,

        "AWAY":
            1.0 / away_odds,
    }


    total = sum(
        raw.values()
    )


    if total <= 0:
        return None


    return {
        pick:
            probability
            / total

        for pick, probability
        in raw.items()
    }


def load_latest_odds():
    """
    Load odds rows ordered oldest -> newest.

    Since odds_map[match_id] is overwritten on every row,
    the final value for each match becomes the latest
    recorded odds row.

    One bookmaker row is used per match because the current
    database does not yet define a preferred bookmaker policy.
    """

    query = text(
        """
        SELECT
            id,
            match_id,
            bookmaker,
            home_win,
            draw,
            away_win,
            recorded_at
        FROM odds
        WHERE
            home_win IS NOT NULL
            AND draw IS NOT NULL
            AND away_win IS NOT NULL
        ORDER BY
            recorded_at ASC,
            id ASC
        """
    )


    odds_map = {}


    with engine.connect() as connection:

        rows = connection.execute(
            query
        )


        for row in rows:

            item = row._mapping


            match_id = int(
                item[
                    "match_id"
                ]
            )


            odds_map[
                match_id
            ] = {
                "id":
                    item[
                        "id"
                    ],

                "bookmaker":
                    item[
                        "bookmaker"
                    ],

                "home_odds":
                    item[
                        "home_win"
                    ],

                "draw_odds":
                    item[
                        "draw"
                    ],

                "away_odds":
                    item[
                        "away_win"
                    ],

                "recorded_at":
                    item[
                        "recorded_at"
                    ],
            }


    return odds_map


def get_pick_name(
    pick,
    match,
):

    if pick == "HOME":

        return (
            match
            .home_team
            .name
        )


    if pick == "AWAY":

        return (
            match
            .away_team
            .name
        )


    return "Draw"


# ============================================================
# MAIN
# ============================================================

def run():

    print()
    print("=" * 100)
    print(
        "ANALITIKO LIVE VALUE RESEARCH"
    )
    print("=" * 100)

    print()
    print(
        f"VALUE edge threshold: "
        f"{VALUE_EDGE_THRESHOLD:.1f}%"
    )

    print(
        f"ELITE VALUE edge threshold: "
        f"{ELITE_VALUE_EDGE_THRESHOLD:.1f}%"
    )

    print()
    print(
        "IMPORTANT:"
    )

    print(
        "VALUE thresholds are research defaults."
    )

    print(
        "They are not yet historically validated."
    )

    print(
        "RAW frozen ML probabilities are used because "
        "calibration testing did not improve log loss."
    )


    # ========================================================
    # LOAD ODDS
    # ========================================================

    odds_map = (
        load_latest_odds()
    )


    print()
    print(
        f"Matches with stored odds: "
        f"{len(odds_map)}"
    )


    # ========================================================
    # DB
    # ========================================================

    db = SessionLocal()


    try:

        now = datetime.utcnow()

        until = (
            now
            + timedelta(
                days=DAYS_AHEAD
            )
        )


        # ====================================================
        # UPCOMING MATCHES
        # ====================================================

        matches = (
            db.query(
                Match
            )
            .filter(
                Match.match_date
                >= now
            )
            .filter(
                Match.match_date
                <= until
            )
            .filter(
                Match.status
                == "NS"
            )
            .order_by(
                Match.match_date.asc()
            )
            .all()
        )


        print(
            f"Upcoming matches: "
            f"{len(matches)}"
        )


        if not matches:

            print()
            print(
                "No upcoming matches."
            )

            return


        match_ids = [
            match.id
            for match
            in matches
        ]


        # ====================================================
        # LATEST SAVED PRE-MATCH ML SNAPSHOT
        # ====================================================

        snapshots = (
            db.query(
                MLPredictionSnapshot
            )
            .filter(
                MLPredictionSnapshot
                .match_id
                .in_(
                    match_ids
                )
            )
            .order_by(
                MLPredictionSnapshot
                .created_at
                .desc()
            )
            .all()
        )


        snapshot_map = {}


        for snapshot in snapshots:

            if (
                snapshot.match_id
                not in snapshot_map
            ):

                snapshot_map[
                    snapshot.match_id
                ] = snapshot


        print(
            f"Upcoming matches with ML snapshot: "
            f"{len(snapshot_map)}"
        )


        # ====================================================
        # COVERAGE COUNTERS
        # ====================================================

        matches_with_snapshot = 0

        matches_with_odds = 0

        matches_with_both = 0


        # ====================================================
        # VALUE CALCULATION
        # ====================================================

        value_picks = []


        for match in matches:

            snapshot = (
                snapshot_map.get(
                    match.id
                )
            )


            odds = (
                odds_map.get(
                    match.id
                )
            )


            if snapshot is not None:

                matches_with_snapshot += 1


            if odds is not None:

                matches_with_odds += 1


            if (
                snapshot is None
                or odds is None
            ):

                continue


            matches_with_both += 1


            # =================================================
            # MARKET PROBABILITY
            # =================================================

            market = normalize_market(
                odds[
                    "home_odds"
                ],
                odds[
                    "draw_odds"
                ],
                odds[
                    "away_odds"
                ],
            )


            if market is None:

                continue


            # =================================================
            # FROZEN ML SNAPSHOT PROBABILITIES
            # =================================================

            model_probabilities = {
                "HOME":
                    normalize_probability(
                        snapshot
                        .home_probability
                    ),

                "DRAW":
                    normalize_probability(
                        snapshot
                        .draw_probability
                    ),

                "AWAY":
                    normalize_probability(
                        snapshot
                        .away_probability
                    ),
            }


            if any(
                probability is None
                for probability
                in model_probabilities.values()
            ):

                continue


            # =================================================
            # EDGES
            # =================================================

            edges = {
                pick:
                    (
                        model_probabilities[
                            pick
                        ]
                        -
                        market[
                            pick
                        ]
                    )
                    * 100

                for pick
                in [
                    "HOME",
                    "DRAW",
                    "AWAY",
                ]
            }


            # =================================================
            # EXPECTED VALUE
            # =================================================

            odds_by_pick = {
                "HOME":
                    float(
                        odds[
                            "home_odds"
                        ]
                    ),

                "DRAW":
                    float(
                        odds[
                            "draw_odds"
                        ]
                    ),

                "AWAY":
                    float(
                        odds[
                            "away_odds"
                        ]
                    ),
            }


            expected_values = {
                pick:
                    (
                        model_probabilities[
                            pick
                        ]
                        *
                        odds_by_pick[
                            pick
                        ]
                        -
                        1.0
                    )
                    * 100

                for pick
                in [
                    "HOME",
                    "DRAW",
                    "AWAY",
                ]
            }


            # =================================================
            # BEST VALUE SIDE
            # =================================================

            best_pick = max(
                edges,
                key=edges.get,
            )


            best_edge = (
                edges[
                    best_pick
                ]
            )


            if (
                best_edge
                < VALUE_EDGE_THRESHOLD
            ):

                continue


            model_probability = (
                model_probabilities[
                    best_pick
                ]
            )


            market_probability = (
                market[
                    best_pick
                ]
            )


            market_odds = (
                odds_by_pick[
                    best_pick
                ]
            )


            fair_odds = (
                1.0
                / model_probability
                if model_probability > 0
                else None
            )


            expected_value = (
                expected_values[
                    best_pick
                ]
            )


            # =================================================
            # ELITE VALUE
            #
            # ELITE VALUE =
            # frozen ELITE signal + enough market edge
            # =================================================

            is_elite_value = (
                bool(
                    snapshot
                    .is_elite_pick
                )
                and
                best_edge
                >= ELITE_VALUE_EDGE_THRESHOLD
            )


            # =================================================
            # MODEL PICK VS VALUE PICK
            # =================================================

            same_as_model_pick = (
                snapshot.pick
                == best_pick
            )


            value_picks.append(
                {
                    "match":
                        match,

                    "snapshot":
                        snapshot,

                    "odds":
                        odds,

                    "pick":
                        best_pick,

                    "model_pick":
                        snapshot.pick,

                    "same_as_model_pick":
                        same_as_model_pick,

                    "edge":
                        best_edge,

                    "model_probability":
                        model_probability
                        * 100,

                    "market_probability":
                        market_probability
                        * 100,

                    "market_odds":
                        market_odds,

                    "fair_odds":
                        fair_odds,

                    "expected_value":
                        expected_value,

                    "is_elite_value":
                        is_elite_value,

                    "all_edges":
                        edges,
                }
            )


        # ====================================================
        # SORT
        #
        # ELITE VALUE first,
        # then highest edge,
        # then Analitiko Score.
        # ====================================================

        value_picks.sort(
            key=lambda item: (
                item[
                    "is_elite_value"
                ],

                item[
                    "edge"
                ],

                item[
                    "snapshot"
                ].analitiko_score,
            ),
            reverse=True,
        )


        # ====================================================
        # COVERAGE
        # ====================================================

        print()
        print("=" * 100)
        print(
            "LIVE COVERAGE"
        )
        print("=" * 100)

        print(
            f"Upcoming matches: "
            f"{len(matches)}"
        )

        print(
            f"With ML snapshot: "
            f"{matches_with_snapshot}"
        )

        print(
            f"With odds: "
            f"{matches_with_odds}"
        )

        print(
            f"With both ML + odds: "
            f"{matches_with_both}"
        )

        print(
            f"Value candidates: "
            f"{len(value_picks)}"
        )


        # ====================================================
        # OUTPUT
        # ====================================================

        print()
        print("=" * 100)
        print(
            "LIVE VALUE PICKS"
        )
        print("=" * 100)


        if not value_picks:

            print()
            print(
                "No current VALUE signals."
            )

            print()
            print(
                "This can mean:"
            )

            print(
                "- upcoming match has no saved odds"
            )

            print(
                "- upcoming match has no ML snapshot"
            )

            print(
                "- model/market edge is below 5%"
            )


        for index, item in enumerate(
            value_picks,
            start=1,
        ):

            match = (
                item[
                    "match"
                ]
            )

            snapshot = (
                item[
                    "snapshot"
                ]
            )

            odds = (
                item[
                    "odds"
                ]
            )


            signal = (
                "ELITE VALUE"
                if item[
                    "is_elite_value"
                ]
                else "VALUE"
            )


            pick_name = (
                get_pick_name(
                    item[
                        "pick"
                    ],
                    match,
                )
            )


            print()
            print(
                "-" * 100
            )

            print(
                f"#{index} [{signal}]"
            )


            print(
                f"Match ID: "
                f"{match.id}"
            )


            print(
                f"League: "
                f"{match.league.name}"
            )


            print(
                f"Match: "
                f"{match.home_team.name}"
                f" vs "
                f"{match.away_team.name}"
            )


            print(
                f"Date: "
                f"{match.match_date}"
            )


            print()
            print(
                f"Value pick: "
                f"{item['pick']}"
                f" ({pick_name})"
            )


            print(
                f"Frozen ML pick: "
                f"{item['model_pick']}"
            )


            print(
                f"Value pick = ML pick: "
                f"{item['same_as_model_pick']}"
            )


            print()
            print(
                f"Model probability: "
                f"{item['model_probability']:.1f}%"
            )


            print(
                f"Market probability: "
                f"{item['market_probability']:.1f}%"
            )


            print(
                f"Edge: "
                f"{item['edge']:+.1f}%"
            )


            print(
                f"Expected value: "
                f"{item['expected_value']:+.1f}%"
            )


            print()
            print(
                f"Market odds: "
                f"{item['market_odds']:.2f}"
            )


            if (
                item[
                    "fair_odds"
                ]
                is not None
            ):

                print(
                    f"Model fair odds: "
                    f"{item['fair_odds']:.2f}"
                )


            print()
            print(
                f"Bookmaker: "
                f"{odds['bookmaker']}"
            )


            print(
                f"Odds recorded: "
                f"{odds['recorded_at']}"
            )


            print()
            print(
                "All edges:"
            )


            print(
                f"  HOME: "
                f"{item['all_edges']['HOME']:+.1f}%"
            )


            print(
                f"  DRAW: "
                f"{item['all_edges']['DRAW']:+.1f}%"
            )


            print(
                f"  AWAY: "
                f"{item['all_edges']['AWAY']:+.1f}%"
            )


            print()
            print(
                f"Analitiko Score: "
                f"{snapshot.analitiko_score:.1f}"
            )


            print(
                f"Confidence: "
                f"{snapshot.confidence:.1f}%"
            )


            print(
                f"Strong: "
                f"{snapshot.is_strong_pick}"
            )


            print(
                f"Elite: "
                f"{snapshot.is_elite_pick}"
            )


            print(
                f"Signal level: "
                f"{snapshot.confidence_level}"
            )


        print()
        print("=" * 100)

        print(
            "Research only. "
            "Do not infer profitability from the "
            "3-match historical odds sample."
        )

        print("=" * 100)


    finally:

        db.close()


if __name__ == "__main__":
    run()