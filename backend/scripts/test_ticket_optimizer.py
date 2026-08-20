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


def print_result(
    title,
    result,
):

    print()
    print("=" * 100)
    print(title)
    print("=" * 100)

    print(
        f"Success: "
        f"{result['success']}"
    )

    print(
        f"Candidates: "
        f"{result['candidates_found']}"
    )

    print(
        f"Requested selections: "
        f"{result['requested_selections']}"
    )

    print(
        f"Target odds: "
        f"{result['target_odds']}"
    )

    print(
        f"Message: "
        f"{result['message']}"
    )

    if not result[
        "success"
    ]:
        return

    print()

    for index, item in enumerate(
        result[
            "selections"
        ],
        start=1,
    ):

        print(
            f"{index}. "
            f"{item['match']}"
        )

        print(
            f"   League: "
            f"{item['league']}"
        )

        print(
            f"   Pick: "
            f"{item['market']} "
            f"{item['selection']}"
        )

        print(
            f"   Odds: "
            f"{item['odds']}"
        )

        print(
            f"   Raw probability: "
            f"{item['raw_probability']}%"
        )

        print(
            f"   Calibrated: "
            f"{item['calibrated_probability']}%"
        )

        print(
            f"   Edge: "
            f"{item['edge']:+.2f}%"
        )

        print(
            f"   EV: "
            f"{item['expected_value']:+.2f}%"
        )

        print(
            f"   Quality: "
            f"{item['quality_score']} "
            f"({item['quality_tier']})"
        )

        print(
            f"   Uncertainty: "
            f"{item['uncertainty']}%"
        )

        print()

    metrics = (
        result[
            "metrics"
        ]
    )

    print("-" * 100)

    print(
        f"Total odds: "
        f"{metrics['total_odds']}"
    )

    print(
        f"Estimated probability: "
        f"{metrics['estimated_probability']}%"
    )

    print(
        f"Naive probability: "
        f"{metrics['naive_probability']}%"
    )

    print(
        f"Average quality: "
        f"{metrics['average_quality']}"
    )

    print(
        f"Average uncertainty: "
        f"{metrics['average_uncertainty']}%"
    )

    print(
        f"Average edge: "
        f"{metrics['average_edge']:+.2f}%"
    )

    print(
        f"Average EV: "
        f"{metrics['average_ev']:+.2f}%"
    )

    print(
        f"Correlation penalty: "
        f"{metrics['correlation_penalty']}"
    )

    print(
        f"Optimizer score: "
        f"{metrics['optimizer_score']}"
    )


def run():

    db = SessionLocal()

    try:

        now = datetime.utcnow()

        end = (
            now
            + timedelta(
                days=2
            )
        )

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

            print_result(
                strategy,
                result,
            )

        print()
        print("=" * 100)
        print(
            "STATUS: OK"
        )
        print("=" * 100)

    finally:

        db.close()


if __name__ == "__main__":
    run()