from datetime import datetime, timedelta

from sqlalchemy import text

from app.database.database import SessionLocal


def run():
    db = SessionLocal()

    now = datetime.utcnow()
    end = now + timedelta(days=2)

    print()
    print("=" * 80)
    print("ANALITIKO LIVE COVERAGE AUDIT")
    print("=" * 80)
    print(f"Window: {now} -> {end}")
    print()

    try:
        matches = db.execute(
            text(
                """
                SELECT
                    m.id,
                    m.external_id,
                    m.match_date,
                    m.status,
                    l.name AS league_name,
                    ht.id AS home_team_id,
                    ht.name AS home_team_name,
                    at.id AS away_team_id,
                    at.name AS away_team_name
                FROM matches m
                JOIN leagues l
                    ON l.id = m.league_id
                JOIN teams ht
                    ON ht.id = m.home_team_id
                JOIN teams at
                    ON at.id = m.away_team_id
                WHERE m.match_date >= :start
                  AND m.match_date <= :end
                ORDER BY m.match_date ASC
                """
            ),
            {
                "start": now,
                "end": end,
            },
        ).mappings().all()

        print(f"Upcoming matches: {len(matches)}")
        print()

        total = len(matches)

        with_history = 0
        missing_history = 0

        with_ml = 0
        missing_ml = 0

        with_odds = 0
        missing_odds = 0

        fully_ready = 0

        for match in matches:
            match_id = match["id"]

            home_history = db.execute(
                text(
                    """
                    SELECT COUNT(*)
                    FROM team_match_history
                    WHERE team_id = :team_id
                    """
                ),
                {
                    "team_id": match["home_team_id"],
                },
            ).scalar() or 0

            away_history = db.execute(
                text(
                    """
                    SELECT COUNT(*)
                    FROM team_match_history
                    WHERE team_id = :team_id
                    """
                ),
                {
                    "team_id": match["away_team_id"],
                },
            ).scalar() or 0

            has_history = (
                home_history >= 5
                and away_history >= 5
            )

            if has_history:
                with_history += 1
            else:
                missing_history += 1

            ml_snapshot = db.execute(
                text(
                    """
                    SELECT COUNT(*)
                    FROM ml_prediction_snapshots
                    WHERE match_id = :match_id
                    """
                ),
                {
                    "match_id": match_id,
                },
            ).scalar() or 0

            has_ml = ml_snapshot > 0

            if has_ml:
                with_ml += 1
            else:
                missing_ml += 1

            odds_count = db.execute(
                text(
                    """
                    SELECT COUNT(*)
                    FROM odds
                    WHERE match_id = :match_id
                    """
                ),
                {
                    "match_id": match_id,
                },
            ).scalar() or 0

            has_odds = odds_count > 0

            if has_odds:
                with_odds += 1
            else:
                missing_odds += 1

            ready = (
                has_history
                and has_ml
                and has_odds
            )

            if ready:
                fully_ready += 1

            print("-" * 80)
            print(
                f"[{match_id}] "
                f"{match['home_team_name']} "
                f"vs "
                f"{match['away_team_name']}"
            )

            print(
                f"League: "
                f"{match['league_name']}"
            )

            print(
                f"Date: "
                f"{match['match_date']}"
            )

            print(
                f"History: "
                f"HOME={home_history} "
                f"AWAY={away_history} "
                f"=> {'OK' if has_history else 'MISSING'}"
            )

            print(
                f"ML snapshot: "
                f"{'YES' if has_ml else 'NO'}"
            )

            print(
                f"Odds: "
                f"{'YES' if has_odds else 'NO'}"
            )

            print(
                f"READY: "
                f"{'YES' if ready else 'NO'}"
            )

        print()
        print("=" * 80)
        print("COVERAGE SUMMARY")
        print("=" * 80)

        print(
            f"Upcoming matches:      "
            f"{total}"
        )

        print(
            f"Enough history:        "
            f"{with_history}"
        )

        print(
            f"Missing history:       "
            f"{missing_history}"
        )

        print(
            f"With ML snapshot:      "
            f"{with_ml}"
        )

        print(
            f"Missing ML snapshot:   "
            f"{missing_ml}"
        )

        print(
            f"With odds:             "
            f"{with_odds}"
        )

        print(
            f"Missing odds:          "
            f"{missing_odds}"
        )

        print(
            f"Fully ready:           "
            f"{fully_ready}"
        )

        if total > 0:
            coverage = (
                fully_ready
                / total
                * 100
            )

            print(
                f"Full coverage:         "
                f"{coverage:.1f}%"
            )

        print("=" * 80)

    finally:
        db.close()


if __name__ == "__main__":
    run()