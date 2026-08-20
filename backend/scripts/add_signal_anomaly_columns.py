from sqlalchemy import (
    inspect,
    text,
)

from app.database.database import engine


def run():

    inspector = inspect(engine)

    columns = {
        row["name"]
        for row in inspector.get_columns(
            "signal_intelligence"
        )
    }

    statements = []

    if "anomaly_score" not in columns:
        statements.append(
            """
            ALTER TABLE signal_intelligence
            ADD COLUMN anomaly_score FLOAT
            NOT NULL DEFAULT 0.0
            """
        )

    if "anomaly_level" not in columns:
        statements.append(
            """
            ALTER TABLE signal_intelligence
            ADD COLUMN anomaly_level VARCHAR
            NOT NULL DEFAULT 'NORMAL'
            """
        )

    if "requires_review" not in columns:
        statements.append(
            """
            ALTER TABLE signal_intelligence
            ADD COLUMN requires_review INTEGER
            NOT NULL DEFAULT 0
            """
        )

    print()
    print("=" * 100)
    print("ANALITIKO SIGNAL ANOMALY MIGRATION")
    print("=" * 100)

    with engine.begin() as connection:

        for statement in statements:
            connection.execute(
                text(statement)
            )

    if statements:
        print(
            f"Columns added: "
            f"{len(statements)}"
        )
    else:
        print(
            "Columns already exist."
        )

    print("STATUS: OK")
    print("=" * 100)


if __name__ == "__main__":
    run()