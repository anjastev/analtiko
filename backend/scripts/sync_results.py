from datetime import datetime, timezone, timedelta

from app.collectors.api_football import APIFootballClient
from app.database.database import SessionLocal
from app.models.match import Match


FINISHED_STATUSES = {
    "FT",
    "AET",
    "PEN",
}

ACTIVE_OR_PENDING_STATUSES = {
    "NS",
    "TBD",
    "1H",
    "HT",
    "2H",
    "ET",
    "BT",
    "P",
    "SUSP",
    "INT",
}


def run():
    db = SessionLocal()
    client = APIFootballClient()

    now = datetime.now(timezone.utc)

    # Гледаме мечеви од последни 2 дена,
    # бидејќи тие најверојатно можеле да завршат.
    from_time = now - timedelta(days=2)

    updated = 0
    unchanged = 0
    skipped = 0
    failed = 0

    try:
        matches = (
            db.query(Match)
            .filter(
                Match.external_id.isnot(None),
                Match.match_date >= from_time,
                Match.match_date <= now,
            )
            .order_by(
                Match.match_date.asc()
            )
            .limit(30)
            .all()
        )

        print()
        print("=" * 70)
        print("ANALITIKO RESULTS SYNC")
        print("=" * 70)

        print(
            f"Matches to check: {len(matches)}"
        )

        for match in matches:
            print()
            print(
                f"{match.home_team.name} "
                f"vs "
                f"{match.away_team.name}"
            )

            print(
                f"Local status: {match.status}"
            )

            try:
                data = client.get_fixture(
                    match.external_id
                )

                errors = data.get(
                    "errors",
                    {}
                )

                if errors:
                    print(
                        f"API error: {errors}"
                    )

                    skipped += 1
                    continue

                response = data.get(
                    "response",
                    []
                )

                if not response:
                    print(
                        "No fixture returned."
                    )

                    skipped += 1
                    continue

                fixture_data = response[0]

                fixture = fixture_data.get(
                    "fixture",
                    {}
                )

                goals = fixture_data.get(
                    "goals",
                    {}
                )

                status = (
                    fixture
                    .get("status", {})
                    .get("short")
                )

                home_score = goals.get(
                    "home"
                )

                away_score = goals.get(
                    "away"
                )

                changed = False

                # -----------------------------------------
                # STATUS
                # -----------------------------------------

                if (
                    status
                    and match.status != status
                ):
                    match.status = status
                    changed = True

                # -----------------------------------------
                # SCORES
                # -----------------------------------------

                if (
                    home_score is not None
                    and match.home_score != home_score
                ):
                    match.home_score = home_score
                    changed = True

                if (
                    away_score is not None
                    and match.away_score != away_score
                ):
                    match.away_score = away_score
                    changed = True

                # -----------------------------------------
                # SAVE
                # -----------------------------------------

                if changed:
                    db.commit()

                    updated += 1

                    print(
                        "UPDATED"
                    )

                    print(
                        f"Status: {match.status}"
                    )

                    print(
                        f"Score: "
                        f"{match.home_score}"
                        f"-"
                        f"{match.away_score}"
                    )

                else:
                    db.rollback()

                    unchanged += 1

                    print(
                        "No changes."
                    )

            except Exception as error:
                db.rollback()

                failed += 1

                print(
                    f"FAILED: {error}"
                )

        print()
        print("=" * 70)
        print("RESULTS SYNC COMPLETE")
        print("=" * 70)

        print(
            f"Updated: {updated}"
        )

        print(
            f"Unchanged: {unchanged}"
        )

        print(
            f"Skipped: {skipped}"
        )

        print(
            f"Failed: {failed}"
        )

    finally:
        db.close()


if __name__ == "__main__":
    run()