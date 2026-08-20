from app.database.database import (
    SessionLocal,
)

from app.services.backend_health import (
    get_backend_health,
)


REQUIRED_HEALTH_FIELDS = {
    "status",
    "timestamp",
    "upcoming_matches",
    "production_ready_matches",
    "production_coverage",
    "active_signals",
    "value_signals",
    "pending_combinations",
    "fresh_odds_rows",
}


def run():

    db = SessionLocal()

    failures = 0

    try:

        print()
        print("=" * 100)
        print(
            "ANALITIKO API CONTRACT TEST"
        )
        print("=" * 100)

        health = (
            get_backend_health(
                db
            )
        )

        missing = (
            REQUIRED_HEALTH_FIELDS
            - set(
                health.keys()
            )
        )

        if missing:

            failures += 1

            print(
                f"[FAIL] Missing health fields: "
                f"{sorted(missing)}"
            )

        else:

            print(
                "[OK] Health contract"
            )

        print(
            f"[INFO] Status: "
            f"{health['status']}"
        )

        print(
            f"[INFO] Upcoming: "
            f"{health['upcoming_matches']}"
        )

        print(
            f"[INFO] READY: "
            f"{health['production_ready_matches']}"
        )

        print(
            f"[INFO] Coverage: "
            f"{health['production_coverage']}%"
        )

        print(
            f"[INFO] Active signals: "
            f"{health['active_signals']}"
        )

        print(
            f"[INFO] VALUE signals: "
            f"{health['value_signals']}"
        )

        print(
            f"[INFO] Pending combinations: "
            f"{health['pending_combinations']}"
        )

        print(
            f"[INFO] Fresh odds rows: "
            f"{health['fresh_odds_rows']}"
        )

        print()
        print("=" * 100)

        if failures == 0:

            print(
                "STATUS: OK"
            )

        else:

            print(
                f"STATUS: FAILED "
                f"({failures})"
            )

        print("=" * 100)

    finally:

        db.close()


if __name__ == "__main__":
    run()