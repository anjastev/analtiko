from sqlalchemy import text

from app.database.database import (
    Base,
    engine,
)

from app.models.value_prediction_snapshot import (
    ValuePredictionSnapshot,
)


def run():

    print()
    print("=" * 80)
    print(
        "CREATE VALUE PREDICTION SNAPSHOT TABLE"
    )
    print("=" * 80)

    # Importing model registers it with Base metadata.
    Base.metadata.create_all(
        bind=engine,
    )

    print(
        "Table ready: "
        "value_prediction_snapshots"
    )

    print("=" * 80)


if __name__ == "__main__":
    run()