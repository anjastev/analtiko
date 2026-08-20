from sqlalchemy import inspect

from app.database.database import engine


def run():

    print()
    print("=" * 90)
    print("ANALITIKO DATABASE ODDS INSPECTION")
    print("=" * 90)

    inspector = inspect(
        engine
    )

    tables = inspector.get_table_names()

    print()
    print(
        f"Tables found: {len(tables)}"
    )

    print()


    for table in tables:

        columns = inspector.get_columns(
            table
        )

        column_names = [
            column["name"]
            for column
            in columns
        ]


        searchable = " ".join(
            [
                table,
                *column_names,
            ]
        ).lower()


        if any(
            keyword in searchable
            for keyword in [
                "odd",
                "price",
                "bookmaker",
                "market",
                "bet",
            ]
        ):

            print("-" * 90)

            print(
                f"TABLE: {table}"
            )

            print(
                "COLUMNS:"
            )

            for column in columns:

                print(
                    f"  - {column['name']}"
                    f" ({column['type']})"
                )

            print()


    print("=" * 90)


if __name__ == "__main__":
    run()