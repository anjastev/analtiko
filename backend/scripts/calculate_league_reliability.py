from datetime import datetime

from app.database.database import (
    SessionLocal,
)

from app.models.league import League

from app.models.league_reliability import (
    LeagueReliability,
)

from app.services.league_reliability_service import (
    calculate_league_stats,
)


def run():

    db = SessionLocal()

    created = 0
    updated = 0

    try:

        leagues = (
            db.query(League)
            .all()
        )

        print()
        print("=" * 100)
        print(
            "ANALITIKO LEAGUE RELIABILITY"
        )
        print("=" * 100)

        for league in leagues:

            stats = (
                calculate_league_stats(
                    db,
                    league,
                )
            )

            row = (
                db.query(
                    LeagueReliability
                )
                .filter(
                    LeagueReliability.league_id
                    == league.id
                )
                .first()
            )

            if row is None:

                row = (
                    LeagueReliability(
                        league_id=(
                            league.id
                        )
                    )
                )

                db.add(
                    row
                )

                created += 1

            else:

                updated += 1

            row.evaluated_signals = (
                stats[
                    "evaluated_signals"
                ]
            )

            row.wins = (
                stats[
                    "wins"
                ]
            )

            row.losses = (
                stats[
                    "losses"
                ]
            )

            row.hit_rate = (
                stats[
                    "hit_rate"
                ]
            )

            row.average_edge = (
                stats[
                    "average_edge"
                ]
            )

            row.roi = (
                stats[
                    "roi"
                ]
            )

            row.reliability_score = (
                stats[
                    "reliability_score"
                ]
            )

            row.sample_confidence = (
                stats[
                    "sample_confidence"
                ]
            )

            row.updated_at = (
                datetime.utcnow()
            )

            print(
                f"{league.name:<35} "
                f"n="
                f"{stats['evaluated_signals']:<4} "
                f"reliability="
                f"{stats['reliability_score']:.3f} "
                f"confidence="
                f"{stats['sample_confidence']:.2f}"
            )

        db.commit()

        print()
        print("=" * 100)

        print(
            f"Created: "
            f"{created}"
        )

        print(
            f"Updated: "
            f"{updated}"
        )

        print(
            "STATUS: OK"
        )

        print("=" * 100)

    except Exception:

        db.rollback()
        raise

    finally:

        db.close()


if __name__ == "__main__":
    run()