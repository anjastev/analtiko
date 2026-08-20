from sqlalchemy import (
    inspect,
    text,
)

from app.database.database import (
    engine,
)


# ============================================================
# HELPERS
# ============================================================

def table_exists(
    inspector,
    table_name,
):
    return (
        table_name
        in inspector.get_table_names()
    )


def get_columns(
    inspector,
    table_name,
):
    if not table_exists(
        inspector,
        table_name,
    ):
        return set()

    return {
        column["name"]
        for column
        in inspector.get_columns(
            table_name
        )
    }


def scalar_query(
    query,
    params=None,
):
    with engine.connect() as connection:

        result = connection.execute(
            text(
                query
            ),
            params or {},
        )

        value = result.scalar()

        if value is None:
            return 0

        return value


def count_table(
    inspector,
    table_name,
):
    if not table_exists(
        inspector,
        table_name,
    ):
        return 0

    return int(
        scalar_query(
            f'SELECT COUNT(*) '
            f'FROM "{table_name}"'
        )
    )


def count_distinct(
    inspector,
    table_name,
    column_name,
):
    if not table_exists(
        inspector,
        table_name,
    ):
        return 0

    columns = get_columns(
        inspector,
        table_name,
    )

    if column_name not in columns:
        return 0

    return int(
        scalar_query(
            f'SELECT COUNT(DISTINCT "{column_name}") '
            f'FROM "{table_name}"'
        )
    )


def count_where(
    inspector,
    table_name,
    where_clause,
):
    if not table_exists(
        inspector,
        table_name,
    ):
        return 0

    return int(
        scalar_query(
            f'SELECT COUNT(*) '
            f'FROM "{table_name}" '
            f'WHERE {where_clause}'
        )
    )


def find_existing_table(
    inspector,
    candidates,
):
    tables = set(
        inspector.get_table_names()
    )

    for candidate in candidates:

        if candidate in tables:
            return candidate

    return None


def print_status(
    label,
    ok,
):
    status = (
        "OK"
        if ok
        else "MISSING"
    )

    print(
        f"{label:<32}"
        f"{status}"
    )


# ============================================================
# MAIN
# ============================================================

def run():

    print()
    print("=" * 70)
    print(
        "ANALITIKO PIPELINE HEALTH"
    )
    print("=" * 70)

    inspector = inspect(
        engine
    )

    tables = set(
        inspector.get_table_names()
    )

    # ========================================================
    # TABLE DISCOVERY
    # ========================================================

    matches_table = (
        find_existing_table(
            inspector,
            [
                "matches",
                "match",
            ],
        )
    )

    odds_table = (
        find_existing_table(
            inspector,
            [
                "odds",
            ],
        )
    )

    history_table = (
        find_existing_table(
            inspector,
            [
                "team_match_history",
                "team_match_histories",
            ],
        )
    )

    rule_snapshot_table = (
        find_existing_table(
            inspector,
            [
                "prediction_snapshots",
                "prediction_snapshot",
                "predictions",
            ],
        )
    )

    ml_snapshot_table = (
        find_existing_table(
            inspector,
            [
                "ml_prediction_snapshots",
                "ml_prediction_snapshot",
            ],
        )
    )

    value_snapshot_table = (
        find_existing_table(
            inspector,
            [
                "value_prediction_snapshots",
            ],
        )
    )

    official_table = (
        find_existing_table(
            inspector,
            [
                "official_predictions",
                "official_prediction",
            ],
        )
    )

    # ========================================================
    # MATCHES
    # ========================================================

    total_matches = 0
    upcoming_matches = 0
    finished_matches = 0

    if matches_table:

        total_matches = (
            count_table(
                inspector,
                matches_table,
            )
        )

        match_columns = (
            get_columns(
                inspector,
                matches_table,
            )
        )

        if "status" in match_columns:

            upcoming_matches = (
                count_where(
                    inspector,
                    matches_table,
                    "\"status\" = 'NS'",
                )
            )

            finished_matches = (
                count_where(
                    inspector,
                    matches_table,
                    "\"status\" IN ('FT', 'AET', 'PEN')",
                )
            )

    # ========================================================
    # ODDS
    # ========================================================

    odds_rows = 0
    odds_matches = 0

    if odds_table:

        odds_rows = (
            count_table(
                inspector,
                odds_table,
            )
        )

        odds_matches = (
            count_distinct(
                inspector,
                odds_table,
                "match_id",
            )
        )

    # ========================================================
    # HISTORY
    # ========================================================

    history_rows = 0
    history_teams = 0

    if history_table:

        history_rows = (
            count_table(
                inspector,
                history_table,
            )
        )

        history_teams = (
            count_distinct(
                inspector,
                history_table,
                "team_id",
            )
        )

    # ========================================================
    # RULE SNAPSHOTS
    # ========================================================

    rule_snapshots = 0
    rule_evaluated = 0

    if rule_snapshot_table:

        rule_snapshots = (
            count_table(
                inspector,
                rule_snapshot_table,
            )
        )

        rule_columns = (
            get_columns(
                inspector,
                rule_snapshot_table,
            )
        )

        if "correct" in rule_columns:

            rule_evaluated = (
                count_where(
                    inspector,
                    rule_snapshot_table,
                    "\"correct\" IS NOT NULL",
                )
            )

    # ========================================================
    # ML SNAPSHOTS
    # ========================================================

    ml_snapshots = 0
    ml_evaluated = 0

    if ml_snapshot_table:

        ml_snapshots = (
            count_table(
                inspector,
                ml_snapshot_table,
            )
        )

        ml_columns = (
            get_columns(
                inspector,
                ml_snapshot_table,
            )
        )

        if "correct" in ml_columns:

            ml_evaluated = (
                count_where(
                    inspector,
                    ml_snapshot_table,
                    "\"correct\" IS NOT NULL",
                )
            )

    # ========================================================
    # VALUE SNAPSHOTS
    # ========================================================

    value_snapshots = 0
    value_evaluated = 0
    elite_value_snapshots = 0

    if value_snapshot_table:

        value_snapshots = (
            count_table(
                inspector,
                value_snapshot_table,
            )
        )

        value_columns = (
            get_columns(
                inspector,
                value_snapshot_table,
            )
        )

        if "correct" in value_columns:

            value_evaluated = (
                count_where(
                    inspector,
                    value_snapshot_table,
                    "\"correct\" IS NOT NULL",
                )
            )

        if "is_elite_value" in value_columns:

            elite_value_snapshots = (
                count_where(
                    inspector,
                    value_snapshot_table,
                    "\"is_elite_value\" = 1",
                )
            )

    # ========================================================
    # OFFICIAL PREDICTIONS
    # ========================================================

    official_predictions = 0

    if official_table:

        official_predictions = (
            count_table(
                inspector,
                official_table,
            )
        )

    # ========================================================
    # DISPLAY
    # ========================================================

    print()
    print(
        "MATCHES"
    )

    print(
        f"Total:       "
        f"{total_matches}"
    )

    print(
        f"Upcoming:    "
        f"{upcoming_matches}"
    )

    print(
        f"Finished:    "
        f"{finished_matches}"
    )

    print()
    print(
        "ODDS"
    )

    print(
        f"Rows:        "
        f"{odds_rows}"
    )

    print(
        f"Matches:     "
        f"{odds_matches}"
    )

    print()
    print(
        "HISTORY"
    )

    print(
        f"Rows:        "
        f"{history_rows}"
    )

    print(
        f"Teams:       "
        f"{history_teams}"
    )

    print()
    print(
        "RULE PREDICTIONS"
    )

    print(
        f"Snapshots:   "
        f"{rule_snapshots}"
    )

    print(
        f"Evaluated:   "
        f"{rule_evaluated}"
    )

    print()
    print(
        "ML PREDICTIONS"
    )

    print(
        f"Snapshots:   "
        f"{ml_snapshots}"
    )

    print(
        f"Evaluated:   "
        f"{ml_evaluated}"
    )

    print()
    print(
        "VALUE PREDICTIONS"
    )

    print(
        f"Snapshots:   "
        f"{value_snapshots}"
    )

    print(
        f"Elite Value: "
        f"{elite_value_snapshots}"
    )

    print(
        f"Evaluated:   "
        f"{value_evaluated}"
    )

    print()
    print(
        "OFFICIAL"
    )

    print(
        f"Predictions: "
        f"{official_predictions}"
    )

    # ========================================================
    # HEALTH CHECKS
    # ========================================================

    matches_ok = (
        total_matches > 0
    )

    upcoming_ok = (
        upcoming_matches > 0
    )

    odds_ok = (
        odds_rows > 0
    )

    history_ok = (
        history_rows > 0
    )

    ml_ok = (
        ml_snapshots > 0
    )

    value_ok = (
        value_snapshots > 0
    )

    any_evaluation = (
        rule_evaluated > 0
        or ml_evaluated > 0
        or value_evaluated > 0
    )

    print()
    print("=" * 70)
    print(
        "HEALTH"
    )
    print("=" * 70)

    print_status(
        "Matches available",
        matches_ok,
    )

    print_status(
        "Upcoming matches",
        upcoming_ok,
    )

    print_status(
        "Odds available",
        odds_ok,
    )

    print_status(
        "History available",
        history_ok,
    )

    print_status(
        "ML prediction data",
        ml_ok,
    )

    print_status(
        "VALUE prediction data",
        value_ok,
    )

    print_status(
        "Evaluation data",
        any_evaluation,
    )

    # ========================================================
    # INFO
    # ========================================================

    print()
    print(
        "Tables detected:"
    )

    for table in sorted(
        tables
    ):

        print(
            f"  - {table}"
        )

    print()
    print("=" * 70)

    # ========================================================
    # OVERALL
    #
    # Evaluation data is allowed to be missing while current
    # live snapshots are still pending.
    # ========================================================

    core_healthy = all(
        [
            matches_ok,
            odds_ok,
            history_ok,
            ml_ok,
        ]
    )

    if core_healthy:

        print(
            "Pipeline Health: OK"
        )

    else:

        print(
            "Pipeline Health: WARNING"
        )

    print("=" * 70)


if __name__ == "__main__":
    run()