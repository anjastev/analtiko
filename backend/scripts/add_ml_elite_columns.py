from sqlalchemy import (
    inspect,
    text,
)

from app.database.database import (
    engine,
)


TABLE_NAME = (
    "ml_prediction_snapshots"
)


def run():

    inspector = inspect(
        engine
    )


    tables = (
        inspector.get_table_names()
    )


    if TABLE_NAME not in tables:

        print(
            f"Table {TABLE_NAME} "
            "does not exist."
        )

        return


    columns = {
        column["name"]
        for column
        in inspector.get_columns(
            TABLE_NAME
        )
    }


    print(
        f"Existing columns: "
        f"{len(columns)}"
    )


    with engine.begin() as connection:

        if (
            "elite_threshold"
            not in columns
        ):

            connection.execute(
                text(
                    """
                    ALTER TABLE
                    ml_prediction_snapshots
                    ADD COLUMN
                    elite_threshold FLOAT
                    NOT NULL
                    DEFAULT 50.0
                    """
                )
            )

            print(
                "Added: elite_threshold"
            )

        else:

            print(
                "Already exists: "
                "elite_threshold"
            )


        if (
            "is_elite_pick"
            not in columns
        ):

            connection.execute(
                text(
                    """
                    ALTER TABLE
                    ml_prediction_snapshots
                    ADD COLUMN
                    is_elite_pick BOOLEAN
                    NOT NULL
                    DEFAULT 0
                    """
                )
            )

            print(
                "Added: is_elite_pick"
            )

        else:

            print(
                "Already exists: "
                "is_elite_pick"
            )


    print(
        "ML elite migration complete."
    )


if __name__ == "__main__":
    run()