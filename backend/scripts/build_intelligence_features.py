from datetime import (
    datetime,
    timezone,
)

from app.database.database import (
    SessionLocal,
)

from app.models.intelligence_feature_snapshot import (
    IntelligenceFeatureSnapshot,
)

from app.models.match import Match

from app.services.intelligence_features import (
    build_match_features,
)


def run():

    db = SessionLocal()

    now = datetime.now(
        timezone.utc
    )

    created = 0
    failed = 0

    try:

        # SQLite currently stores naive UTC.
        db_now = (
            now.replace(
                tzinfo=None
            )
        )

        matches = (
            db.query(Match)
            .filter(
                Match.match_date
                > db_now
            )
            .order_by(
                Match.match_date.asc()
            )
            .all()
        )

        print()
        print("=" * 100)
        print(
            "ANALITIKO INTELLIGENCE FEATURES"
        )
        print("=" * 100)

        print(
            f"Upcoming matches: "
            f"{len(matches)}"
        )

        for match in matches:

            try:

                features = (
                    build_match_features(
                        db=db,
                        match=match,
                        snapshot_at=now,
                    )
                )

                db.add(
                    IntelligenceFeatureSnapshot(

                        match_id=(
                            match.id
                        ),

                        snapshot_at=(
                            db_now
                        ),

                        **features,
                    )
                )

                created += 1

                print()
                print(
                    f"[OK] "
                    f"{match.home_team.name} "
                    f"vs "
                    f"{match.away_team.name}"
                )

                print(
                    f"  ELO: "
                    f"{features['home_elo']:.0f} "
                    f"vs "
                    f"{features['away_elo']:.0f} "
                    f"(diff "
                    f"{features['elo_difference']:+.0f})"
                )

                print(
                    f"  Form: "
                    f"{features['home_weighted_form']:.3f} "
                    f"vs "
                    f"{features['away_weighted_form']:.3f}"
                )

                print(
                    f"  Adjusted: "
                    f"{features['home_strength_adjusted_form']:.3f} "
                    f"vs "
                    f"{features['away_strength_adjusted_form']:.3f}"
                )

                if (
                    features[
                        "home_market_probability"
                    ]
                    is not None
                ):

                    print(
                        f"  Market: "
                        f"H="
                        f"{features['home_market_probability']:.1f}% "
                        f"D="
                        f"{features['draw_market_probability']:.1f}% "
                        f"A="
                        f"{features['away_market_probability']:.1f}%"
                    )

                else:

                    print(
                        "  Market: unavailable"
                    )

            except Exception as error:

                failed += 1

                print()
                print(
                    f"[FAILED] "
                    f"{match.id} "
                    f"{match.home_team.name} "
                    f"vs "
                    f"{match.away_team.name}"
                )

                print(
                    f"  {type(error).__name__}: "
                    f"{error}"
                )

        db.commit()

        print()
        print("=" * 100)
        print(
            "INTELLIGENCE FEATURE SUMMARY"
        )
        print("=" * 100)

        print(
            f"Created: "
            f"{created}"
        )

        print(
            f"Failed: "
            f"{failed}"
        )

        if failed == 0:

            print(
                "STATUS: OK"
            )

        elif created > 0:

            print(
                "STATUS: PARTIAL"
            )

        else:

            print(
                "STATUS: FAILED"
            )

        print("=" * 100)

        if (
            failed > 0
            and created == 0
        ):

            raise SystemExit(1)

    except Exception:

        db.rollback()
        raise

    finally:

        db.close()


if __name__ == "__main__":
    run()