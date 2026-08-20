from datetime import (
    datetime,
    timedelta,
    timezone,
)

from app.database.database import (
    SessionLocal,
)

from app.models.match import Match

from app.ml.football_feature_builder_v2 import (
    build_football_features_v2,
)


WINDOW_DAYS = 3


def run():

    db = SessionLocal()

    now = datetime.now(
        timezone.utc
    )

    end = (
        now
        + timedelta(
            days=WINDOW_DAYS
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
        missing = 0
        strong_context = 0

        print()
        print("=" * 80)
        print(
            "ANALITIKO V2 FEATURE COVERAGE"
        )
        print("=" * 80)

        print(
            f"Upcoming matches: "
            f"{len(matches)}"
        )

        for match in matches:

            features = (
                build_football_features_v2(
                    db=db,
                    match=match,
                )
            )

            if features is None:

                missing += 1
                continue

            ready += 1

            home_count = (
                features[
                    "_home_venue_count"
                ]
            )

            away_count = (
                features[
                    "_away_venue_count"
                ]
            )

            if (
                home_count >= 5
                and away_count >= 5
            ):

                strong_context += 1

            print()
            print(
                f"[{match.id}] "
                f"{match.home_team.name} "
                f"vs "
                f"{match.away_team.name}"
            )

            print(
                "General history: "
                f"{features['_home_history_count']}"
                "/"
                f"{features['_away_history_count']}"
            )

            print(
                "Venue history: "
                f"{home_count}"
                "/"
                f"{away_count}"
            )

            print(
                "Context PPG: "
                f"{features['home_home_ppg']:.2f}"
                " vs "
                f"{features['away_away_ppg']:.2f}"
            )

        print()
        print("=" * 80)

        print(
            f"Feature-ready: "
            f"{ready}"
        )

        print(
            f"Missing general history: "
            f"{missing}"
        )

        print(
            f"5+ venue matches both teams: "
            f"{strong_context}"
        )

        print(
            "STATUS: OK"
        )

        print("=" * 80)

    finally:

        db.close()


if __name__ == "__main__":
    run()