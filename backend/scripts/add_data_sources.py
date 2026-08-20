from app.database.database import (
    Base,
    SessionLocal,
    engine,
)

from app.models.data_source import DataSource

import app.models


DEFAULT_SOURCES = [
    {
        "name": "API-Football",
        "provider_type": "statistics",
        "sport": "football",
        "priority": 1,
    },
    {
        "name": "API-Football Odds",
        "provider_type": "odds",
        "sport": "football",
        "priority": 1,
    },
]


def run():

    Base.metadata.create_all(
        bind=engine
    )

    db = SessionLocal()

    try:

        for item in DEFAULT_SOURCES:

            existing = (
                db.query(DataSource)
                .filter(
                    DataSource.name
                    == item["name"]
                )
                .first()
            )

            if existing:
                print(
                    f"[EXISTS] "
                    f"{item['name']}"
                )
                continue

            source = DataSource(
                **item
            )

            db.add(source)

            print(
                f"[CREATED] "
                f"{item['name']}"
            )

        db.commit()

        print()
        print(
            "Data sources ready."
        )

    except Exception:

        db.rollback()
        raise

    finally:

        db.close()


if __name__ == "__main__":
    run()