from __future__ import annotations

import os
from datetime import datetime

from fastapi import (
    APIRouter,
    File,
    Header,
    HTTPException,
    UploadFile,
)

from sqlalchemy import (
    inspect,
    text,
)

from app.database.database import (
    engine,
)


router = APIRouter(
    prefix="/admin/database-import",
    tags=["Database Import"],
)


# ============================================================
# SECURITY
# ============================================================

IMPORT_TOKEN = os.getenv(
    "DATABASE_IMPORT_TOKEN"
)


def verify_token(
    token: str | None,
):

    if not IMPORT_TOKEN:

        raise HTTPException(
            status_code=503,
            detail=(
                "Database import is disabled."
            ),
        )

    if token != IMPORT_TOKEN:

        raise HTTPException(
            status_code=401,
            detail="Invalid import token.",
        )


# ============================================================
# IMPORT ORDER
#
# Parent tables must be inserted before tables
# containing foreign keys to them.
# ============================================================

TABLE_ORDER = [

    # Core
    "sports",
    "data_sources",
    "leagues",
    "teams",
    "markets",

    # Matches
    "matches",
    "match_stats",
    "team_match_history",
    "h2h_matches",

    # Historical / state
    "history_sync_states",

    # Odds
    "odds",
    "market_odds",

    # ML / predictions
    "prediction_snapshots",
    "ml_prediction_snapshots",
    "market_predictions",
    "market_evaluation_snapshots",
    "value_prediction_snapshots",

    # Intelligence
    "team_power_ratings",
    "market_consensus_snapshots",
    "intelligence_feature_snapshots",
    "league_reliability",

    # Signals
    "signals",
    "signal_intelligence",

    # CLV
    "clv_snapshots",

    # Tickets
    "combinations",
    "combination_selections",
]


# ============================================================
# HELPERS
# ============================================================

def parse_value(
    value,
    column,
):

    if value is None:
        return None

    column_type = (
        column[
            "type"
        ]
    )

    type_name = (
        column_type
        .__class__
        .__name__
        .upper()
    )

    # ========================================================
    # BOOLEAN
    #
    # SQLite stores booleans as:
    #
    # 0 / 1
    #
    # PostgreSQL requires:
    #
    # False / True
    # ========================================================

    if (
        "BOOL"
        in type_name
    ):

        if isinstance(
            value,
            bool,
        ):

            return value

        if isinstance(
            value,
            int,
        ):

            return bool(
                value
            )

        if isinstance(
            value,
            float,
        ):

            return bool(
                int(
                    value
                )
            )

        if isinstance(
            value,
            str,
        ):

            normalized = (
                value
                .strip()
                .lower()
            )

            if normalized in {
                "1",
                "true",
                "yes",
                "y",
                "on",
            }:

                return True

            if normalized in {
                "0",
                "false",
                "no",
                "n",
                "off",
            }:

                return False

        return bool(
            value
        )

    # ========================================================
    # DATETIME / DATE / TIME
    # ========================================================

    if (
        "DATE"
        in type_name
        or
        "TIME"
        in type_name
    ):

        if isinstance(
            value,
            str,
        ):

            try:

                return (
                    datetime.fromisoformat(
                        value.replace(
                            "Z",
                            "+00:00",
                        )
                    )
                )

            except ValueError:

                return value

    # ========================================================
    # DEFAULT
    # ========================================================

    return value


def get_database_tables():

    inspector = inspect(
        engine
    )

    return set(
        inspector.get_table_names()
    )


def get_columns(
    table_name: str,
):

    inspector = inspect(
        engine
    )

    return {
        column[
            "name"
        ]:
            column

        for column in (
            inspector.get_columns(
                table_name
            )
        )
    }


# ============================================================
# STATUS
# ============================================================

@router.get(
    "/status"
)
def database_import_status(
    x_import_token: str | None = Header(
        default=None
    ),
):

    verify_token(
        x_import_token
    )

    tables = (
        get_database_tables()
    )

    counts = {}

    with engine.connect() as connection:

        for table_name in TABLE_ORDER:

            if table_name not in tables:
                continue

            result = (
                connection.execute(
                    text(
                        f'''
                        SELECT COUNT(*)
                        FROM "{table_name}"
                        '''
                    )
                )
                .scalar()
            )

            counts[
                table_name
            ] = int(
                result
                or 0
            )

    return {
        "status": "ready",
        "database":
            engine.url
            .get_backend_name(),
        "counts": counts,
    }


# ============================================================
# DATABASE IMPORT
# ============================================================

@router.post(
    ""
)
async def import_database(
    file: UploadFile = File(...),

    x_import_token: str | None = Header(
        default=None
    ),
):

    verify_token(
        x_import_token
    )

    # ========================================================
    # FILE VALIDATION
    # ========================================================

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="Missing file.",
        )

    if not (
        file.filename
        .lower()
        .endswith(".json")
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Only JSON database exports "
                "are accepted."
            ),
        )

    # 25 MB is far above the current ~6 MB export,
    # but prevents accidental huge uploads.

    max_size = (
        25
        * 1024
        * 1024
    )

    content = await file.read(
        max_size + 1
    )

    if len(content) > max_size:

        raise HTTPException(
            status_code=413,
            detail=(
                "Database export is too large."
            ),
        )

    # ========================================================
    # JSON
    # ========================================================

    import json

    try:

        payload = json.loads(
            content.decode(
                "utf-8"
            )
        )

    except Exception as error:

        raise HTTPException(
            status_code=400,
            detail=(
                f"Invalid JSON: {error}"
            ),
        )

    if not isinstance(
        payload,
        dict,
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Export root must be "
                "a JSON object."
            ),
        )

    # ========================================================
    # DATABASE STRUCTURE
    # ========================================================

    existing_tables = (
        get_database_tables()
    )

    imported = {}

    skipped = {}

    # ========================================================
    # IMPORT TRANSACTION
    # ========================================================

    try:

        with engine.begin() as connection:

            # ------------------------------------------------
            # Disable FK checks only through deferred
            # constraints where possible.
            #
            # We still insert in dependency order.
            # ------------------------------------------------

            if (
                engine.url
                .get_backend_name()
                == "postgresql"
            ):

                try:

                    connection.execute(
                        text(
                            """
                            SET CONSTRAINTS ALL DEFERRED
                            """
                        )
                    )

                except Exception:

                    # Not every FK is necessarily
                    # DEFERRABLE. Ordered insertion
                    # remains the main protection.

                    pass

            # ------------------------------------------------
            # TABLES
            # ------------------------------------------------

            for table_name in TABLE_ORDER:

                rows = payload.get(
                    table_name,
                    []
                )

                if not rows:

                    imported[
                        table_name
                    ] = 0

                    continue

                if (
                    table_name
                    not in existing_tables
                ):

                    skipped[
                        table_name
                    ] = (
                        "Table does not exist "
                        "in production database."
                    )

                    continue

                columns = (
                    get_columns(
                        table_name
                    )
                )

                valid_column_names = set(
                    columns.keys()
                )

                inserted = 0

                # --------------------------------------------
                # We expect a fresh PostgreSQL database.
                #
                # Refuse to merge into a populated table.
                # This prevents accidental duplicate imports.
                # --------------------------------------------

                existing_count = (
                    connection.execute(
                        text(
                            f'''
                            SELECT COUNT(*)
                            FROM "{table_name}"
                            '''
                        )
                    )
                    .scalar()
                )

                if (
                    int(
                        existing_count
                        or 0
                    )
                    > 0
                ):

                    raise RuntimeError(
                        f"Refusing to import "
                        f"{table_name}: production "
                        f"table already contains "
                        f"{existing_count} rows."
                    )

                for source_row in rows:

                    if not isinstance(
                        source_row,
                        dict,
                    ):
                        continue

                    row = {}

                    for (
                        key,
                        value,
                    ) in source_row.items():

                        if (
                            key
                            not in valid_column_names
                        ):
                            continue

                        row[
                            key
                        ] = parse_value(
                            value,
                            columns[
                                key
                            ],
                        )

                    if not row:
                        continue

                    column_names = list(
                        row.keys()
                    )

                    quoted_columns = (
                        ", ".join(
                            f'"{name}"'
                            for name
                            in column_names
                        )
                    )

                    placeholders = (
                        ", ".join(
                            f":{name}"
                            for name
                            in column_names
                        )
                    )

                    statement = text(
                        f'''
                        INSERT INTO "{table_name}"
                        ({quoted_columns})
                        VALUES ({placeholders})
                        '''
                    )

                    connection.execute(
                        statement,
                        row,
                    )

                    inserted += 1

                imported[
                    table_name
                ] = inserted

            # =================================================
            # RESET POSTGRESQL ID SEQUENCES
            #
            # Explicit IDs were copied from SQLite.
            # PostgreSQL sequences therefore need to move
            # past the largest imported ID.
            # =================================================

            if (
                engine.url
                .get_backend_name()
                == "postgresql"
            ):

                for table_name in TABLE_ORDER:

                    if (
                        table_name
                        not in existing_tables
                    ):
                        continue

                    columns = (
                        get_columns(
                            table_name
                        )
                    )

                    if "id" not in columns:
                        continue

                    sequence_name = (
                        connection.execute(
                            text(
                                """
                                SELECT pg_get_serial_sequence(
                                    :table_name,
                                    'id'
                                )
                                """
                            ),
                            {
                                "table_name":
                                    table_name,
                            },
                        )
                        .scalar()
                    )

                    if not sequence_name:
                        continue

                    max_id = (
                        connection.execute(
                            text(
                                f'''
                                SELECT MAX(id)
                                FROM "{table_name}"
                                '''
                            )
                        )
                        .scalar()
                    )

                    if max_id is None:
                        continue

                    connection.execute(
                        text(
                            """
                            SELECT setval(
                                :sequence_name,
                                :next_value,
                                true
                            )
                            """
                        ),
                        {
                            "sequence_name":
                                sequence_name,

                            "next_value":
                                int(
                                    max_id
                                ),
                        },
                    )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                "Database import failed. "
                f"Transaction rolled back. "
                f"{type(error).__name__}: "
                f"{error}"
            ),
        )

    # ========================================================
    # VERIFY COUNTS
    # ========================================================

    verification = {}

    with engine.connect() as connection:

        for table_name in TABLE_ORDER:

            if (
                table_name
                not in existing_tables
            ):
                continue

            count = (
                connection.execute(
                    text(
                        f'''
                        SELECT COUNT(*)
                        FROM "{table_name}"
                        '''
                    )
                )
                .scalar()
            )

            verification[
                table_name
            ] = int(
                count
                or 0
            )

    return {
        "status":
            "success",

        "filename":
            file.filename,

        "imported":
            imported,

        "skipped":
            skipped,

        "verification":
            verification,

        "message":
            (
                "Database import completed. "
                "Remove this temporary endpoint "
                "after verification."
            ),
    }