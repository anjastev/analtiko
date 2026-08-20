from app.database.database import (
    Base,
    SessionLocal,
    engine,
)

from app.models.sport import Sport

import app.models


SPORTS = [
    {
        "code": "football",
        "name": "Football",
    },
    {
        "code": "basketball",
        "name": "Basketball",
    },
    {
        "code": "tennis",
        "name": "Tennis",
    },
]


def run():

    Base.metadata.create_all(
        bind=engine
    )

    db = SessionLocal()

    try:

        for item in SPORTS:

            existing = (
                db.query(Sport)
                .filter(
                    Sport.code
                    == item["code"]
                )
                .first()
            )

            if existing:
                print(
                    f"[EXISTS] "
                    f"{item['name']}"
                )
                continue

            db.add(
                Sport(
                    **item
                )
            )

            print(
                f"[CREATED] "
                f"{item['name']}"
            )

        db.commit()

    except Exception:

        db.rollback()
        raise

    finally:

        db.close()


if __name__ == "__main__":
    run()