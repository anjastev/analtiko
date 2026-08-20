from sqlalchemy import (
    inspect,
    text,
)

from app.database.database import (
    engine,
)


MIGRATIONS = {
    "signals": [
        (
            "bookmaker",
            "VARCHAR",
        ),
        (
            "expected_value",
            "FLOAT",
        ),
        (
            "is_value",
            "BOOLEAN NOT NULL DEFAULT 0",
        ),
        (
            "odds_recorded_at",
            "DATETIME",
        ),
        (
            "actual_result",
            "VARCHAR",
        ),
        (
            "correct",
            "BOOLEAN",
        ),
        (
            "profit",
            "FLOAT",
        ),
        (
            "roi",
            "FLOAT",
        ),
        (
            "evaluated_at",
            "DATETIME",
        ),
    ],

    "combinations": [
        (
            "profit",
            "FLOAT",
        ),
        (
            "roi",
            "FLOAT",
        ),
        (
            "evaluated_at",
            "DATETIME",
        ),
    ],

    "combination_selections": [
        (
            "actual_result",
            "VARCHAR",
        ),
        (
            "correct",
            "BOOLEAN",
        ),
        (
            "profit",
            "FLOAT",
        ),
        (
            "evaluated_at",
            "DATETIME",
        ),
    ],
}


def get_columns(
    table_name,
):

    inspector = inspect(
        engine
    )

    return {
        column["name"]
        for column in inspector.get_columns(
            table_name
        )
    }


def run():

    created = 0
    existing = 0

    print()
    print("=" * 100)
    print(
        "ANALITIKO VALUE/EVALUATION MIGRATION"
    )
    print("=" * 100)

    with engine.begin() as connection:

        for table_name, columns in (
            MIGRATIONS.items()
        ):

            current = (
                get_columns(
                    table_name
                )
            )

            print()
            print(
                f"TABLE: "
                f"{table_name}"
            )

            for (
                column_name,
                column_type,
            ) in columns:

                if (
                    column_name
                    in current
                ):

                    existing += 1

                    print(
                        f"  [EXISTS] "
                        f"{column_name}"
                    )

                    continue

                statement = (
                    f"ALTER TABLE "
                    f"{table_name} "
                    f"ADD COLUMN "
                    f"{column_name} "
                    f"{column_type}"
                )

                connection.execute(
                    text(
                        statement
                    )
                )

                created += 1

                print(
                    f"  [ADDED] "
                    f"{column_name}"
                )

    print()
    print("=" * 100)

    print(
        f"Columns added: "
        f"{created}"
    )

    print(
        f"Already existing: "
        f"{existing}"
    )

    print(
        "STATUS: OK"
    )

    print("=" * 100)


if __name__ == "__main__":
    run()