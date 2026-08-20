from datetime import (
    datetime,
    timedelta,
)

from app.database.database import (
    SessionLocal,
)

from app.services.ticket_optimizer import (
    optimize_ticket,
)


def run():

    db = SessionLocal()

    failures = 0

    try:

        now = datetime.utcnow()

        end = (
            now
            + timedelta(
                days=2
            )
        )

        print()
        print("=" * 100)
        print(
            "ANALITIKO TICKET OPTIMIZER AUDIT"
        )
        print("=" * 100)

        for strategy in [
            "SAFE",
            "BALANCED",
            "AGGRESSIVE",
        ]:

            result = (
                optimize_ticket(
                    db,
                    strategy=strategy,
                    date_from=now,
                    date_to=end,
                )
            )

            print()
            print(
                strategy
            )

            print(
                f"  Candidates: "
                f"{result['candidates_found']}"
            )

            if not result[
                "success"
            ]:

                print(
                    "  No ticket generated."
                )

                continue

            selections = (
                result[
                    "selections"
                ]
            )

            match_ids = [
                item[
                    "match_id"
                ]
                for item in selections
            ]

            if (
                len(match_ids)
                !=
                len(
                    set(
                        match_ids
                    )
                )
            ):

                failures += 1

                print(
                    "  [FAIL] Duplicate match"
                )

            else:

                print(
                    "  [OK] Unique matches"
                )

            invalid_quality = [
                item
                for item in selections
                if (
                    item[
                        "quality_score"
                    ] < 60
                )
            ]

            if invalid_quality:

                failures += 1

                print(
                    "  [FAIL] Low quality selection"
                )

            else:

                print(
                    "  [OK] Quality gate"
                )

            invalid_ev = [
                item
                for item in selections
                if (
                    item[
                        "expected_value"
                    ] <= 0
                )
            ]

            if invalid_ev:

                failures += 1

                print(
                    "  [FAIL] Non-positive EV"
                )

            else:

                print(
                    "  [OK] EV gate"
                )

            print(
                f"  Total odds: "
                f"{result['metrics']['total_odds']}"
            )

            print(
                f"  Estimated probability: "
                f"{result['metrics']['estimated_probability']}%"
            )

            print(
                f"  Avg quality: "
                f"{result['metrics']['average_quality']}"
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

        if failures:

            raise SystemExit(1)

    finally:

        db.close()


if __name__ == "__main__":
    run()