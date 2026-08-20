from app.database.database import (
    Base,
    engine,
)

import app.models


def run():

    print()
    print("=" * 100)
    print(
        "ANALITIKO PRODUCTION DATABASE INITIALIZATION"
    )
    print("=" * 100)

    Base.metadata.create_all(
        bind=engine
    )

    print()
    print(
        "Database tables created."
    )

    print()
    print(
        "STATUS: OK"
    )

    print("=" * 100)


if __name__ == "__main__":
    run()