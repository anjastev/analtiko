from pathlib import Path

from app.database.database import (
    SessionLocal,
)

from app.models.match import Match

from app.ml.football_feature_builder_v2 import (
    build_football_features_v2,
)


BASE_DIR = (
    Path(__file__)
    .resolve()
    .parents[1]
)


EXPECTED_MODELS = [
    (
        BASE_DIR
        / "models"
        / "over25_model_v2_candidate.joblib"
    ),
    (
        BASE_DIR
        / "models"
        / "btts_model_v2_candidate.joblib"
    ),
]


def run():

    db = SessionLocal()

    checks = []
    try:

        print()
        print("=" * 80)
        print(
            "ANALITIKO MARKET MODEL V2 TEST"
        )
        print("=" * 80)

        for model_file in (
            EXPECTED_MODELS
        ):

            exists = (
                model_file.exists()
            )

            checks.append(
                exists
            )

            print(
                (
                    "[OK] "
                    if exists
                    else "[FAIL] "
                )
                + model_file.name
            )

        matches = (
            db.query(Match)
            .order_by(
                Match.match_date.desc()
            )
            .limit(100)
            .all()
        )

        feature_ready = 0

        for match in matches:

            features = (
                build_football_features_v2(
                    db=db,
                    match=match,
                )
            )

            if features is not None:
                feature_ready += 1

        feature_check = (
            feature_ready > 0
        )

        checks.append(
            feature_check
        )

        print()
        print(
            (
                "[OK] "
                if feature_check
                else "[WARN] "
            )
            + "V2 feature-ready matches: "
            + str(
                feature_ready
            )
        )

        print()
        print("=" * 80)

        passed = sum(
            1
            for item in checks
            if item
        )

        print(
            f"Checks passed: "
            f"{passed}/{len(checks)}"
        )

        print(
            "STATUS: "
            + (
                "OK"
                if passed
                == len(checks)
                else "PARTIAL"
            )
        )

        print("=" * 80)

    finally:

        db.close()


if __name__ == "__main__":
    run()