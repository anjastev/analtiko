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
            "ANALITIKO TICKET STRATEGY REPORT"
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
                "-" * 50
            )

            if not result[
                "success"
            ]:

                print(
                    "No eligible ticket."
                )

                print(
                    f"Candidates: "
                    f"{result['candidates_found']}"
                )

                continue

            metrics = (
                result[
                    "metrics"
                ]
            )

            print(
                f"Selections: "
                f"{len(result['selections'])}"
            )

            print(
                f"Candidates: "
                f"{result['candidates_found']}"
            )

            print(
                f"Total odds: "
                f"{metrics['total_odds']}"
            )

            print(
                f"Estimated probability: "
                f"{metrics['estimated_probability']}%"
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

            print()

            for item in result[
                "selections"
            ]:

                print(
                    f"  {item['match']}"
                )

                print(
                    f"    "
                    f"{item['market']} "
                    f"{item['selection']} | "
                    f"{item['odds']} | "
                    f"Q={item['quality_score']} | "
                    f"U={item['uncertainty']}%"
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