from datetime import (
    datetime,
    timedelta,
    timezone,
)

from app.database.database import (
    SessionLocal,
)

from app.models.match import Match

from app.services.match_data_quality import (
    evaluate_match_data_quality,
)


UPCOMING_DAYS = 3


FINISHED_STATUSES = {
    "FT",
    "AET",
    "PEN",
}


def run():

    db = SessionLocal()

    now = datetime.now(
        timezone.utc
    )

    end = (
        now
        + timedelta(
            days=UPCOMING_DAYS
        )
    )

    try:

        matches = (
            db.query(Match)
            .filter(
                Match.match_date
                >= now,

                Match.match_date
                <= end,

                ~Match.status.in_(
                    FINISHED_STATUSES
                ),
            )
            .order_by(
                Match.match_date.asc()
            )
            .all()
        )

        ready = 0
        partial = 0
        blocked = 0

        print()
        print("=" * 100)
        print(
            "ANALITIKO PRODUCTION READINESS"
        )
        print("=" * 100)

        for match in matches:

            quality = (
                evaluate_match_data_quality(
                    db=db,
                    match=match,
                )
            )

            status = (
                quality[
                    "status"
                ]
            )

            if status == "READY":
                ready += 1

            elif status == "PARTIAL":
                partial += 1

            else:
                blocked += 1

            print(
                f"[{status:<7}] "
                f"{match.id} | "
                f"{match.home_team.name} "
                f"vs "
                f"{match.away_team.name}"
            )

        total = len(
            matches
        )

        coverage = (
            ready
            / total
            * 100.0
            if total
            else 0.0
        )

        print()
        print("=" * 100)

        print(
            f"Ready:    "
            f"{ready}/{total}"
        )

        print(
            f"Partial:  "
            f"{partial}"
        )

        print(
            f"Blocked:  "
            f"{blocked}"
        )

        print(
            f"Production coverage: "
            f"{coverage:.1f}%"
        )

        print()

        if coverage >= 80.0:

            print(
                "STATUS: GOOD"
            )

        elif coverage >= 50.0:

            print(
                "STATUS: PARTIAL"
            )

        else:

            print(
                "STATUS: BLOCKED"
            )

        print("=" * 100)

    finally:

        db.close()


if __name__ == "__main__":
    run()