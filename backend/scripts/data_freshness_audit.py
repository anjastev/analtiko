from datetime import (
    datetime,
    timedelta,
    timezone,
)

from app.database.database import (
    SessionLocal,
)

from app.models.match import Match
from app.models.team_match_history import (
    TeamMatchHistory,
)


UPCOMING_DAYS = 3

FRESH_DAYS = 45

MIN_GENERAL_HISTORY = 5
MIN_VENUE_HISTORY = 5


def get_history(
    db,
    team_id,
    before_date,
    venue=None,
):

    query = (
        db.query(
            TeamMatchHistory
        )
        .filter(
            TeamMatchHistory.team_id
            == team_id,

            TeamMatchHistory.match_date
            < before_date,
        )
    )

    if venue is not None:

        query = query.filter(
            TeamMatchHistory.venue
            == venue
        )

    return (
        query
        .order_by(
            TeamMatchHistory.match_date
            .desc()
        )
        .all()
    )


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

        total = len(
            matches
        )

        basic_ready = 0
        venue_ready = 0
        fresh_ready = 0
        production_ready = 0

        print()
        print("=" * 100)
        print(
            "ANALITIKO LIVE DATA FRESHNESS AUDIT"
        )
        print("=" * 100)

        print(
            f"Upcoming matches: "
            f"{total}"
        )

        for match in matches:

            home_all = (
                get_history(
                    db,
                    match.home_team_id,
                    match.match_date,
                )
            )

            away_all = (
                get_history(
                    db,
                    match.away_team_id,
                    match.match_date,
                )
            )

            home_venue = (
                get_history(
                    db,
                    match.home_team_id,
                    match.match_date,
                    venue="home",
                )
            )

            away_venue = (
                get_history(
                    db,
                    match.away_team_id,
                    match.match_date,
                    venue="away",
                )
            )

            basic_ok = (
                len(home_all)
                >= MIN_GENERAL_HISTORY
                and
                len(away_all)
                >= MIN_GENERAL_HISTORY
            )

            venue_ok = (
                len(home_venue)
                >= MIN_VENUE_HISTORY
                and
                len(away_venue)
                >= MIN_VENUE_HISTORY
            )

            home_latest = (
                home_all[0].match_date
                if home_all
                else None
            )

            away_latest = (
                away_all[0].match_date
                if away_all
                else None
            )

            freshness_cutoff = (
                match.match_date
                - timedelta(
                    days=FRESH_DAYS
                )
            )

            fresh_ok = (
                home_latest is not None
                and
                away_latest is not None
                and
                home_latest
                >= freshness_cutoff
                and
                away_latest
                >= freshness_cutoff
            )

            production_ok = (
                basic_ok
                and venue_ok
                and fresh_ok
            )

            if basic_ok:
                basic_ready += 1

            if venue_ok:
                venue_ready += 1

            if fresh_ok:
                fresh_ready += 1

            if production_ok:
                production_ready += 1

            if not production_ok:

                print()
                print(
                    f"[{match.id}] "
                    f"{match.home_team.name} "
                    f"vs "
                    f"{match.away_team.name}"
                )

                print(
                    f"  General: "
                    f"{len(home_all)}/"
                    f"{len(away_all)} "
                    f"{'OK' if basic_ok else 'MISS'}"
                )

                print(
                    f"  Venue: "
                    f"{len(home_venue)}/"
                    f"{len(away_venue)} "
                    f"{'OK' if venue_ok else 'MISS'}"
                )

                print(
                    f"  Latest: "
                    f"{home_latest} | "
                    f"{away_latest}"
                )

                print(
                    f"  Fresh <= "
                    f"{FRESH_DAYS} days: "
                    f"{'OK' if fresh_ok else 'MISS'}"
                )

        print()
        print("=" * 100)

        print(
            f"Basic history ready: "
            f"{basic_ready}/{total}"
        )

        print(
            f"Venue history ready: "
            f"{venue_ready}/{total}"
        )

        print(
            f"Fresh history ready: "
            f"{fresh_ready}/{total}"
        )

        print(
            f"Production-data ready: "
            f"{production_ready}/{total}"
        )

        coverage = (
            (
                production_ready
                / total
                * 100.0
            )
            if total
            else 0.0
        )

        print(
            f"Production coverage: "
            f"{coverage:.1f}%"
        )

        print()

        if coverage >= 80:

            print(
                "STATUS: GOOD"
            )

        elif coverage >= 50:

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