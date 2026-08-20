from app.collectors.api_football import (
    APIFootballClient,
)


SEARCH_TERMS = [
    "double",
    "chance",
    "1x",
    "x2",
]


def run():

    client = APIFootballClient()

    data = (
        client.get_odds_bets()
    )

    errors = data.get(
        "errors"
    )

    if errors:

        print(
            f"API errors: {errors}"
        )

        return

    rows = data.get(
        "response",
        []
    )

    print()
    print("=" * 100)
    print(
        "API-FOOTBALL DOUBLE CHANCE DISCOVERY"
    )
    print("=" * 100)

    print(
        f"Total bet definitions: "
        f"{len(rows)}"
    )

    found = 0

    for row in rows:

        bet_id = row.get(
            "id"
        )

        name = str(
            row.get(
                "name",
                ""
            )
        )

        normalized = (
            name
            .strip()
            .lower()
        )

        if any(
            term in normalized
            for term in SEARCH_TERMS
        ):

            found += 1

            print(
                f"{bet_id:>4} | "
                f"{name}"
            )

    print()
    print(
        f"Possible DC bets: "
        f"{found}"
    )

    print("=" * 100)


if __name__ == "__main__":
    run()