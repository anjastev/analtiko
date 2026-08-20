from datetime import datetime

from sqlalchemy import text

from app.database.database import (
    SessionLocal,
    engine,
)

from app.models.match import Match

from app.models.ml_prediction_snapshot import (
    MLPredictionSnapshot,
)

from app.models.value_prediction_snapshot import (
    ValuePredictionSnapshot,
)


# ============================================================
# CONFIG
# ============================================================

MODEL_VERSION = "logistic_regression_v2"

VALUE_EDGE_THRESHOLD = 5.0

ELITE_VALUE_EDGE_THRESHOLD = 8.0


# ============================================================
# HELPERS
# ============================================================

def normalize_probability(value):

    if value is None:
        return None

    value = float(value)

    if value > 1.5:
        return value / 100.0

    return value


def parse_datetime(value):
    """
    SQLite raw SQL queries may return DATETIME columns
    as strings. SQLAlchemy DateTime model fields require
    real Python datetime objects.
    """

    if value is None:
        return None

    if isinstance(
        value,
        datetime,
    ):
        return value

    if isinstance(
        value,
        str,
    ):

        value = value.strip()

        if not value:
            return None

        # First try standard ISO parsing.
        try:
            return datetime.fromisoformat(
                value
            )
        except ValueError:
            pass

        # Fallback formats.
        formats = [
            "%Y-%m-%d %H:%M:%S.%f",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%S",
        ]

        for fmt in formats:

            try:
                return datetime.strptime(
                    value,
                    fmt,
                )
            except ValueError:
                continue

    raise ValueError(
        f"Could not parse datetime value: {value!r}"
    )


def normalize_market(
    home_odds,
    draw_odds,
    away_odds,
):

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
            probability / total
        for pick, probability
        in raw.items()
    }


def load_latest_odds():

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
                    parse_datetime(
                        item[
                            "recorded_at"
                        ]
                    ),
            }

    return odds_map


def values_equal(
    old_value,
    new_value,
    tolerance=0.001,
):

    if (
        old_value is None
        and new_value is None
    ):
        return True

    if (
        old_value is None
        or new_value is None
    ):
        return False

    return (
        abs(
            float(old_value)
            - float(new_value)
        )
        <= tolerance
    )


def same_value_snapshot(
    existing,
    new_data,
):

    if existing is None:
        return False

    string_fields = [
        "model_version",
        "bookmaker",
        "value_pick",
        "model_pick",
    ]

    boolean_fields = [
        "is_strong_pick",
        "is_elite_pick",
        "is_value_pick",
        "is_elite_value",
        "same_as_model_pick",
    ]

    float_fields = [
        "model_probability",
        "market_probability",
        "edge",
        "market_odds",
        "fair_odds",
        "expected_value",
        "analitiko_score",
        "ml_confidence",
    ]

    for field in string_fields:

        if (
            getattr(
                existing,
                field,
            )
            != new_data[
                field
            ]
        ):
            return False

    for field in boolean_fields:

        if (
            bool(
                getattr(
                    existing,
                    field,
                )
            )
            != bool(
                new_data[
                    field
                ]
            )
        ):
            return False

    for field in float_fields:

        if not values_equal(
            getattr(
                existing,
                field,
            ),
            new_data[
                field
            ],
        ):
            return False

    # Odds timestamp is also meaningful.
    existing_odds_time = (
        existing
        .odds_recorded_at
    )

    new_odds_time = (
        new_data[
            "odds_recorded_at"
        ]
    )

    if (
        existing_odds_time
        != new_odds_time
    ):
        return False

    return True


# ============================================================
# MAIN
# ============================================================

def run():

    print()
    print("=" * 100)
    print(
        "SNAPSHOT LIVE VALUE PREDICTIONS"
    )
    print("=" * 100)

    print(
        f"VALUE threshold: "
        f"{VALUE_EDGE_THRESHOLD:.1f}%"
    )

    print(
        f"ELITE VALUE threshold: "
        f"{ELITE_VALUE_EDGE_THRESHOLD:.1f}%"
    )

    odds_map = (
        load_latest_odds()
    )

    print()
    print(
        f"Matches with odds: "
        f"{len(odds_map)}"
    )

    db = SessionLocal()

    try:

        now = datetime.utcnow()

        # ====================================================
        # UPCOMING MATCHES ONLY
        # ====================================================

        matches = (
            db.query(
                Match
            )
            .filter(
                Match.match_date
                > now
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
            return

        match_ids = [
            match.id
            for match
            in matches
        ]

        # ====================================================
        # LATEST ML SNAPSHOT PER MATCH
        # ====================================================

        ml_snapshots = (
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

        ml_map = {}

        for snapshot in ml_snapshots:

            if (
                snapshot.match_id
                not in ml_map
            ):
                ml_map[
                    snapshot.match_id
                ] = snapshot

        print(
            f"Upcoming matches with ML snapshot: "
            f"{len(ml_map)}"
        )

        # ====================================================
        # COUNTERS
        # ====================================================

        saved = 0
        unchanged = 0
        skipped_missing = 0
        skipped_edge = 0

        value_count = 0
        elite_value_count = 0

        # ====================================================
        # BUILD VALUE SNAPSHOTS
        # ====================================================

        for match in matches:

            ml = ml_map.get(
                match.id
            )

            odds = odds_map.get(
                match.id
            )

            if (
                ml is None
                or odds is None
            ):

                skipped_missing += 1
                continue

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

                skipped_missing += 1
                continue

            probabilities = {
                "HOME":
                    normalize_probability(
                        ml.home_probability
                    ),

                "DRAW":
                    normalize_probability(
                        ml.draw_probability
                    ),

                "AWAY":
                    normalize_probability(
                        ml.away_probability
                    ),
            }

            if any(
                probability is None
                for probability
                in probabilities.values()
            ):

                skipped_missing += 1
                continue

            edges = {
                pick:
                    (
                        probabilities[
                            pick
                        ]
                        - market[
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

            value_pick = max(
                edges,
                key=edges.get,
            )

            edge = float(
                edges[
                    value_pick
                ]
            )

            if (
                edge
                < VALUE_EDGE_THRESHOLD
            ):

                skipped_edge += 1
                continue

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

            model_probability = float(
                probabilities[
                    value_pick
                ]
            )

            market_probability = float(
                market[
                    value_pick
                ]
            )

            market_odds = float(
                odds_by_pick[
                    value_pick
                ]
            )

            fair_odds = (
                1.0
                / model_probability
                if model_probability > 0
                else None
            )

            expected_value = (
                (
                    model_probability
                    * market_odds
                )
                - 1.0
            ) * 100

            is_elite_value = (
                bool(
                    ml.is_elite_pick
                )
                and
                edge
                >= ELITE_VALUE_EDGE_THRESHOLD
            )

            same_as_model_pick = (
                ml.pick
                == value_pick
            )

            new_data = {
                "model_version":
                    MODEL_VERSION,

                "bookmaker":
                    odds[
                        "bookmaker"
                    ],

                "value_pick":
                    value_pick,

                "model_pick":
                    ml.pick,

                "model_probability":
                    model_probability
                    * 100,

                "market_probability":
                    market_probability
                    * 100,

                "edge":
                    edge,

                "market_odds":
                    market_odds,

                "fair_odds":
                    fair_odds,

                "expected_value":
                    expected_value,

                "analitiko_score":
                    float(
                        ml.analitiko_score
                    ),

                "ml_confidence":
                    float(
                        ml.confidence
                    ),

                "is_strong_pick":
                    bool(
                        ml.is_strong_pick
                    ),

                "is_elite_pick":
                    bool(
                        ml.is_elite_pick
                    ),

                "is_value_pick":
                    True,

                "is_elite_value":
                    bool(
                        is_elite_value
                    ),

                "same_as_model_pick":
                    bool(
                        same_as_model_pick
                    ),

                "odds_recorded_at":
                    odds[
                        "recorded_at"
                    ],
            }

            # =================================================
            # CHECK LATEST PENDING VALUE SNAPSHOT
            # =================================================

            existing = (
                db.query(
                    ValuePredictionSnapshot
                )
                .filter(
                    ValuePredictionSnapshot
                    .match_id
                    == match.id
                )
                .filter(
                    ValuePredictionSnapshot
                    .actual_result
                    .is_(
                        None
                    )
                )
                .order_by(
                    ValuePredictionSnapshot
                    .created_at
                    .desc()
                )
                .first()
            )

            if same_value_snapshot(
                existing,
                new_data,
            ):

                unchanged += 1

                print()
                print(
                    f"[UNCHANGED] "
                    f"{match.home_team.name}"
                    f" vs "
                    f"{match.away_team.name}"
                )

                continue

            # =================================================
            # SAVE NEW SNAPSHOT
            # =================================================

            snapshot = (
                ValuePredictionSnapshot(
                    match_id=
                        match.id,

                    model_version=
                        new_data[
                            "model_version"
                        ],

                    bookmaker=
                        new_data[
                            "bookmaker"
                        ],

                    value_pick=
                        new_data[
                            "value_pick"
                        ],

                    model_pick=
                        new_data[
                            "model_pick"
                        ],

                    model_probability=
                        new_data[
                            "model_probability"
                        ],

                    market_probability=
                        new_data[
                            "market_probability"
                        ],

                    edge=
                        new_data[
                            "edge"
                        ],

                    market_odds=
                        new_data[
                            "market_odds"
                        ],

                    fair_odds=
                        new_data[
                            "fair_odds"
                        ],

                    expected_value=
                        new_data[
                            "expected_value"
                        ],

                    analitiko_score=
                        new_data[
                            "analitiko_score"
                        ],

                    ml_confidence=
                        new_data[
                            "ml_confidence"
                        ],

                    is_strong_pick=
                        new_data[
                            "is_strong_pick"
                        ],

                    is_elite_pick=
                        new_data[
                            "is_elite_pick"
                        ],

                    is_value_pick=
                        new_data[
                            "is_value_pick"
                        ],

                    is_elite_value=
                        new_data[
                            "is_elite_value"
                        ],

                    same_as_model_pick=
                        new_data[
                            "same_as_model_pick"
                        ],

                    odds_recorded_at=
                        new_data[
                            "odds_recorded_at"
                        ],
                )
            )

            db.add(
                snapshot
            )

            saved += 1
            value_count += 1

            if is_elite_value:
                elite_value_count += 1

            print()
            print(
                f"[VALUE] "
                f"{match.home_team.name}"
                f" vs "
                f"{match.away_team.name}"
            )

            print(
                f"Pick: "
                f"{value_pick}"
            )

            print(
                f"Edge: "
                f"{edge:+.1f}%"
            )

            print(
                f"Odds: "
                f"{market_odds:.2f}"
            )

            print(
                f"Odds recorded: "
                f"{new_data['odds_recorded_at']}"
            )

            print(
                f"Elite Value: "
                f"{is_elite_value}"
            )

        # ====================================================
        # COMMIT
        # ====================================================

        db.commit()

        print()
        print("=" * 100)

        print(
            f"Saved: "
            f"{saved}"
        )

        print(
            f"Unchanged: "
            f"{unchanged}"
        )

        print(
            f"Skipped missing data: "
            f"{skipped_missing}"
        )

        print(
            f"Skipped below edge threshold: "
            f"{skipped_edge}"
        )

        print(
            f"VALUE snapshots saved: "
            f"{value_count}"
        )

        print(
            f"ELITE VALUE snapshots saved: "
            f"{elite_value_count}"
        )

        print("=" * 100)

    except Exception:

        db.rollback()
        raise

    finally:

        db.close()


if __name__ == "__main__":
    run()