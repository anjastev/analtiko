from app.database.database import (
    Base,
    SessionLocal,
    engine,
)

from app.models.market import Market

import app.models


FOOTBALL_MARKETS = [
    {
        "sport": "football",
        "code": "1X2",
        "name": "Match Result",
        "category": "result",
    },
    {
        "sport": "football",
        "code": "DC",
        "name": "Double Chance",
        "category": "result",
    },
    {
        "sport": "football",
        "code": "OU_15",
        "name": "Over/Under 1.5",
        "category": "goals",
    },
    {
        "sport": "football",
        "code": "OU_25",
        "name": "Over/Under 2.5",
        "category": "goals",
    },
    {
        "sport": "football",
        "code": "OU_35",
        "name": "Over/Under 3.5",
        "category": "goals",
    },
    {
        "sport": "football",
        "code": "BTTS",
        "name": "Both Teams To Score",
        "category": "goals",
    },
    {
        "sport": "football",
        "code": "HOME_TG_05",
        "name": "Home Team Over 0.5 Goals",
        "category": "team_goals",
    },
    {
        "sport": "football",
        "code": "HOME_TG_15",
        "name": "Home Team Over 1.5 Goals",
        "category": "team_goals",
    },
    {
        "sport": "football",
        "code": "AWAY_TG_05",
        "name": "Away Team Over 0.5 Goals",
        "category": "team_goals",
    },
    {
        "sport": "football",
        "code": "AWAY_TG_15",
        "name": "Away Team Over 1.5 Goals",
        "category": "team_goals",
    },
]


def run():

    Base.metadata.create_all(
        bind=engine
    )

    db = SessionLocal()

    try:

        for item in FOOTBALL_MARKETS:

            existing = (
                db.query(Market)
                .filter(
                    Market.sport
                    == item["sport"],
                    Market.code
                    == item["code"],
                )
                .first()
            )

            if existing:
                print(
                    f"[EXISTS] "
                    f"{item['code']}"
                )
                continue

            db.add(
                Market(
                    **item
                )
            )

            print(
                f"[CREATED] "
                f"{item['code']} - "
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