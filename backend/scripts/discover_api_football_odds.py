from app.collectors.api_football import (
    APIFootballClient,
)


INTERESTING_TERMS = [
    "winner",
    "double",
    "chance",
    "goals",
    "over",
    "under",
    "both",
    "teams",
    "score",
]


def run():

    client = (
        APIFootballClient()
    )

    data = (
        client.get_odds_bets()
    )

    errors = (
        data.get(
            "errors"
        )
    )

    if errors:

        print(
            f"API errors: "
            f"{errors}"
        )

        return

    rows = (
        data.get(
            "response",
            []
        )
    )

    print()
    print("=" * 100)
    print(
        "API-FOOTBALL ODDS BET DISCOVERY"
    )
    print("=" * 100)

    print(
        f"Bet definitions: "
        f"{len(rows)}"
    )

    print()

    for row in rows:

        bet_id = (
            row.get(
                "id"
            )
        )

        name = str(
            row.get(
                "name",
                ""
            )
        )

        normalized = (
            name.lower()
        )

        if any(
            term in normalized
            for term in INTERESTING_TERMS
        ):

            print(
                f"{bet_id:>4} | "
                f"{name}"
            )

    print()
    print("=" * 100)
    print(
        "STATUS: OK"
    )
    print("=" * 100)


if __name__ == "__main__":
    run()