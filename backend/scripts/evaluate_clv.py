from sqlalchemy import func

from app.database.database import (
    SessionLocal,
)

from app.models.clv_snapshot import (
    CLVSnapshot,
)


def run():

    db = SessionLocal()

    try:

        rows = (
            db.query(
                CLVSnapshot
            )
            .filter(
                CLVSnapshot.status
                == "CLOSED",

                CLVSnapshot.clv_pct
                .isnot(None),
            )
            .all()
        )

        positive = sum(
            1
            for row in rows
            if row.clv_pct > 0
        )

        negative = sum(
            1
            for row in rows
            if row.clv_pct < 0
        )

        flat = (
            len(rows)
            - positive
            - negative
        )

        average = (
            sum(
                row.clv_pct
                for row in rows
            )
            / len(rows)
            if rows
            else 0.0
        )

        print()
        print("=" * 100)
        print(
            "ANALITIKO CLV PERFORMANCE"
        )
        print("=" * 100)

        print(
            f"Closed signals: "
            f"{len(rows)}"
        )

        print(
            f"Positive CLV: "
            f"{positive}"
        )

        print(
            f"Negative CLV: "
            f"{negative}"
        )

        print(
            f"Flat: "
            f"{flat}"
        )

        print(
            f"Average CLV: "
            f"{average:+.2f}%"
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