from app.database.database import (
    Base,
    engine,
)

import app.models


def run():

    print()
    print("=" * 100)
    print(
        "ANALITIKO INTELLIGENCE V2 TABLES"
    )
    print("=" * 100)

    Base.metadata.create_all(
        bind=engine
    )

    print(
        "team_power_ratings: ready"
    )

    print(
        "market_consensus_snapshots: ready"
    )

    print(
        "intelligence_feature_snapshots: ready"
    )

    print()
    print(
        "STATUS: OK"
    )

    print("=" * 100)


if __name__ == "__main__":
    run()