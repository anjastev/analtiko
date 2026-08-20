from app.database.database import (
    Base,
    engine,
)

import app.models


def run():

    print()
    print("=" * 100)
    print(
        "ANALITIKO INTELLIGENCE BATCH 2 TABLES"
    )
    print("=" * 100)

    Base.metadata.create_all(
        bind=engine
    )

    print(
        "signal_intelligence: ready"
    )

    print(
        "league_reliability: ready"
    )

    print(
        "clv_snapshots: ready"
    )

    print()
    print(
        "STATUS: OK"
    )

    print("=" * 100)


if __name__ == "__main__":
    run()