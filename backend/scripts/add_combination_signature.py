from sqlalchemy import (
    inspect,
    text,
)

from app.database.database import engine


def run():

    inspector = inspect(
        engine
    )

    columns = {
        column["name"]
        for column
        in inspector.get_columns(
            "combinations"
        )
    }

    if "signature" in columns:

        print(
            "Combination signature "
            "already exists."
        )

        return

    with engine.begin() as connection:

        connection.execute(
            text(
                """
                ALTER TABLE combinations
                ADD COLUMN signature VARCHAR
                """
            )
        )

    print(
        "Combination signature added."
    )


if __name__ == "__main__":
    run()