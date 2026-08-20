BOOKMAKER_PRIORITY = [
    "Bet365",
    "Pinnacle",
    "Betfair",
    "Bwin",
    "Unibet",
]


def choose_bookmaker(
    bookmakers: list[dict],
) -> dict | None:

    for preferred_name in BOOKMAKER_PRIORITY:

        for bookmaker in bookmakers:

            if (
                bookmaker["name"].lower()
                == preferred_name.lower()
            ):
                return bookmaker

    if bookmakers:
        return bookmakers[0]

    return None


def find_bet(
    bookmaker: dict,
    bet_name: str,
) -> dict | None:

    for bet in bookmaker.get(
        "bets",
        [],
    ):
        if bet["name"].lower() == bet_name.lower():
            return bet

    return None


def find_value(
    bet: dict | None,
    value_name: str,
) -> float | None:

    if not bet:
        return None

    for item in bet.get(
        "values",
        [],
    ):
        if (
            item["value"].lower()
            == value_name.lower()
        ):
            try:
                return float(item["odd"])
            except (ValueError, TypeError):
                return None

    return None


def parse_odds_response(
    api_response: dict,
) -> dict | None:

    responses = api_response.get(
        "response",
        [],
    )

    if not responses:
        return None

    bookmakers = responses[0].get(
        "bookmakers",
        [],
    )

    bookmaker = choose_bookmaker(
        bookmakers
    )

    if not bookmaker:
        return None

    match_winner = find_bet(
        bookmaker,
        "Match Winner",
    )

    goals = find_bet(
        bookmaker,
        "Goals Over/Under",
    )

    btts = find_bet(
        bookmaker,
        "Both Teams Score",
    )

    return {
        "bookmaker": bookmaker["name"],

        "home_win": find_value(
            match_winner,
            "Home",
        ),

        "draw": find_value(
            match_winner,
            "Draw",
        ),

        "away_win": find_value(
            match_winner,
            "Away",
        ),

        "over_25": find_value(
            goals,
            "Over 2.5",
        ),

        "under_25": find_value(
            goals,
            "Under 2.5",
        ),

        "btts_yes": find_value(
            btts,
            "Yes",
        ),

        "btts_no": find_value(
            btts,
            "No",
        ),
    }