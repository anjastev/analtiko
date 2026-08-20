from __future__ import annotations

from sqlalchemy.orm import Session

from app.services.ticket_optimizer import (
    optimize_ticket,
)


def optimize_multiple_tickets(
    db: Session,
    *,
    strategies: list[str],
    date_from,
    date_to,
    leagues=None,
    exclude_leagues=None,
    min_probability=None,
):

    results = []

    used_signatures = set()

    for strategy in strategies:

        result = (
            optimize_ticket(
                db,
                strategy=strategy,
                date_from=date_from,
                date_to=date_to,
                leagues=leagues,
                exclude_leagues=(
                    exclude_leagues
                ),
                min_probability=(
                    min_probability
                ),
            )
        )

        if not result[
            "success"
        ]:

            results.append(
                result
            )

            continue

        signature = tuple(
            sorted(
                item[
                    "signal_id"
                ]
                for item in result[
                    "selections"
                ]
            )
        )

        if signature in used_signatures:

            result[
                "duplicate_of_previous"
            ] = True

        else:

            result[
                "duplicate_of_previous"
            ] = False

            used_signatures.add(
                signature
            )

        results.append(
            result
        )

    return results