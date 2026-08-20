from app.database.database import (
    Base,
    engine,
)

import app.models


def run():

    Base.metadata.create_all(
        bind=engine
    )

    print()
    print("=" * 60)
    print(
        "ANALITIKO MARKET ODDS"
    )
    print("=" * 60)
    print(
        "Table market_odds is ready."
    )
    print("=" * 60)


if __name__ == "__main__":
    run()