import json
from pathlib import Path

from sqlalchemy import inspect

from app.database.database import engine


OUTPUT_FILE = (
    Path(__file__)
    .resolve()
    .parents[1]
    / "database_export.json"
)


def serialize(value):

    if value is None:
        return None

    if hasattr(
        value,
        "isoformat",
    ):
        return value.isoformat()

    return value


def run():

    inspector = inspect(
        engine
    )

    table_names = (
        inspector.get_table_names()
    )

    export = {}

    print()
    print("=" * 100)
    print(
        "ANALITIKO DATABASE EXPORT"
    )
    print("=" * 100)

    with engine.connect() as connection:

        for table_name in table_names:

            table = (
                connection.exec_driver_sql(
                    f'SELECT * FROM "{table_name}"'
                )
            )

            columns = list(
                table.keys()
            )

            rows = []

            for row in table:

                data = {}

                for (
                    column,
                    value,
                ) in zip(
                    columns,
                    row,
                ):

                    data[
                        column
                    ] = serialize(
                        value
                    )

                rows.append(
                    data
                )

            export[
                table_name
            ] = rows

            print(
                f"{table_name:<40} "
                f"{len(rows)}"
            )

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            export,
            file,
            ensure_ascii=False,
            indent=2,
        )

    print()
    print(
        f"Saved: {OUTPUT_FILE}"
    )

    print()
    print(
        "STATUS: OK"
    )

    print("=" * 100)


if __name__ == "__main__":
    run()