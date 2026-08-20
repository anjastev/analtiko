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
    print("=" * 70)
    print(
        "MARKET EVALUATION SNAPSHOTS"
    )
    print("=" * 70)

    print(
        "Table ready: "
        "market_evaluation_snapshots"
    )

    print("=" * 70)


if __name__ == "__main__":
    run()