from app.database.database import (
    SessionLocal,
)

from app.services.elo_service import (
    rebuild_all_ratings,
)


def run():

    db = SessionLocal()

    try:

        print()
        print("=" * 100)
        print(
            "ANALITIKO ELO REBUILD"
        )
        print("=" * 100)

        result = (
            rebuild_all_ratings(
                db
            )
        )

        print(
            f"Finished matches: "
            f"{result['matches']}"
        )

        print(
            f"Teams rated: "
            f"{result['teams']}"
        )

        print(
            f"Rating rows: "
            f"{result['rows_created']}"
        )

        print()
        print(
            "STATUS: OK"
        )

        print("=" * 100)

    finally:

        db.close()


if __name__ == "__main__":
    run()