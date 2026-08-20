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
        "HISTORY SYNC STATES"
    )
    print("=" * 70)

    print(
        "Table ready: "
        "history_sync_states"
    )

    print("=" * 70)


if __name__ == "__main__":
    run()