from datetime import (
    datetime,
    timedelta,
    timezone,
)

from app.database.database import (
    SessionLocal,
)

from app.models.match import Match

from app.services.history_freshness import (
    team_data_ready,
)


UPCOMING_DAYS = 3


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
            "ANALITIKO POST HISTORY SYNC AUDIT"
        )
        print("=" * 100)

        for match in matches:

            home = (
                team_data_ready(
                    db=db,
                    team_id=(
                        match.home_team_id
                    ),
                    before_date=(
                        match.match_date
                    ),
                    venue="home",
                )
            )

            away = (
                team_data_ready(
                    db=db,
                    team_id=(
                        match.away_team_id
                    ),
                    before_date=(
                        match.match_date
                    ),
                    venue="away",
                )
            )

            match_ready = (
                home[
                    "ready"
                ]
                and
                away[
                    "ready"
                ]
            )

            if match_ready:

                ready += 1

                status = (
                    "READY"
                )

            elif (
                home[
                    "general_count"
                ] > 0
                or
                away[
                    "general_count"
                ] > 0
            ):

                partial += 1

                status = (
                    "PARTIAL"
                )

            else:

                blocked += 1

                status = (
                    "BLOCKED"
                )

            print()
            print(
                f"[{status}] "
                f"{match.home_team.name} "
                f"vs "
                f"{match.away_team.name}"
            )

            print(
                "  HOME "
                f"general="
                f"{home['general_count']} "
                f"venue="
                f"{home['venue_count']} "
                f"fresh="
                f"{home['fresh']}"
            )

            print(
                "  AWAY "
                f"general="
                f"{away['general_count']} "
                f"venue="
                f"{away['venue_count']} "
                f"fresh="
                f"{away['fresh']}"
            )

        total = len(
            matches
        )

        coverage = (
            (
                ready
                / total
                * 100.0
            )
            if total
            else 0.0
        )

        print()
        print("=" * 100)

        print(
            f"Ready: "
            f"{ready}/{total}"
        )

        print(
            f"Partial: "
            f"{partial}"
        )

        print(
            f"Blocked: "
            f"{blocked}"
        )

        print(
            f"Production coverage: "
            f"{coverage:.1f}%"
        )

        if coverage >= 80:

            status = (
                "GOOD"
            )

        elif coverage >= 50:

            status = (
                "PARTIAL"
            )

        else:

            status = (
                "BLOCKED"
            )

        print(
            f"STATUS: "
            f"{status}"
        )

        print("=" * 100)

    finally:

        db.close()


if __name__ == "__main__":
    run()