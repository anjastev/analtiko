from __future__ import annotations

from app.models.market_odds import (
    MarketOdds,
)

from app.services.market_odds_service import (
    get_market,
    is_odds_fresh,
)


# ============================================================
# MARKET DEFINITIONS
# ============================================================

MARKET_SELECTIONS = {

    "1X2": [
        "HOME",
        "DRAW",
        "AWAY",
    ],

    "DC": [
        "1X",
        "X2",
        "12",
    ],

    "OU_25": [
        "OVER",
        "UNDER",
    ],

    "BTTS": [
        "YES",
        "NO",
    ],
}


# These markets contain mutually-exclusive outcomes.
#
# Therefore bookmaker margin can be removed by
# normalizing implied probabilities.

NO_VIG_MARKETS = {
    "1X2",
    "OU_25",
    "BTTS",
}


# DC selections overlap:
#
# 1X = HOME OR DRAW
# X2 = DRAW OR AWAY
# 12 = HOME OR AWAY
#
# They MUST NOT be normalized together.

OVERLAPPING_MARKETS = {
    "DC",
}


# ============================================================
# BASIC PRICE MATH
# ============================================================

def implied_probability_from_odds(
    odds: float,
) -> float:

    odds = float(
        odds
    )

    if odds <= 1.0:

        raise ValueError(
            "Decimal odds must be greater than 1.0"
        )

    return (
        100.0
        / odds
    )


def calculate_expected_value(
    *,
    model_probability: float,
    odds: float,
) -> float:

    probability = (
        float(
            model_probability
        )
        / 100.0
    )

    decimal_odds = float(
        odds
    )

    # EV per 1 unit stake:
    #
    # p * decimal_odds - 1
    #
    # converted to percentage.

    return (
        (
            probability
            * decimal_odds
        )
        - 1.0
    ) * 100.0


# ============================================================
# LATEST QUOTE FOR ONE SELECTION
# ============================================================

def get_latest_selection_quote(
    db,
    *,
    match_id: int,
    market_id: int,
    selection: str,
    bookmaker: str,
    reference_time=None,
    max_age_hours: int = 12,
):

    row = (
        db.query(
            MarketOdds
        )
        .filter(
            MarketOdds.match_id
            == match_id,

            MarketOdds.market_id
            == market_id,

            MarketOdds.bookmaker
            == bookmaker,

            MarketOdds.selection
            == selection,
        )
        .order_by(
            MarketOdds.recorded_at
            .desc(),

            MarketOdds.id
            .desc(),
        )
        .first()
    )

    if row is None:
        return None

    if not (
        is_odds_fresh(
            row,
            reference_time=(
                reference_time
            ),
            max_age_hours=(
                max_age_hours
            ),
        )
    ):
        return None

    if (
        row.odds is None
        or float(
            row.odds
        ) <= 1.0
    ):
        return None

    return row


# ============================================================
# COMPLETE BOOKMAKER MARKET
#
# Only needed for mutually-exclusive markets where we can
# legitimately remove bookmaker margin.
# ============================================================

def get_latest_bookmaker_market(
    db,
    *,
    match_id: int,
    market_code: str,
    bookmaker: str,
    sport: str = "football",
    reference_time=None,
    max_age_hours: int = 12,
):

    market = (
        get_market(
            db=db,
            sport=sport,
            market_code=(
                market_code
            ),
        )
    )

    if market is None:
        return None

    selections = (
        MARKET_SELECTIONS.get(
            market_code
        )
    )

    if not selections:
        return None

    result = {}

    for selection in selections:

        row = (
            get_latest_selection_quote(
                db,
                match_id=(
                    match_id
                ),
                market_id=(
                    market.id
                ),
                selection=(
                    selection
                ),
                bookmaker=(
                    bookmaker
                ),
                reference_time=(
                    reference_time
                ),
                max_age_hours=(
                    max_age_hours
                ),
            )
        )

        if row is None:
            return None

        result[
            selection
        ] = row

    return result


# ============================================================
# NO-VIG
#
# ONLY for mutually-exclusive outcomes.
# ============================================================

def calculate_no_vig_probabilities(
    market_rows: dict,
):

    raw = {}

    for (
        selection,
        row,
    ) in market_rows.items():

        odds = float(
            row.odds
        )

        if odds <= 1.0:
            return None

        raw[
            selection
        ] = (
            1.0
            / odds
        )

    total = sum(
        raw.values()
    )

    if total <= 0:
        return None

    return {

        selection:
            (
                probability
                / total
                * 100.0
            )

        for (
            selection,
            probability,
        ) in raw.items()
    }


# ============================================================
# VALUE CALCULATION
# ============================================================

def calculate_quote_value(
    *,
    market_code: str,
    selection_row,
    model_probability: float,
    no_vig: dict | None = None,
):

    odds = float(
        selection_row.odds
    )

    # --------------------------------------------------------
    # MUTUALLY EXCLUSIVE MARKET
    # --------------------------------------------------------

    if (
        market_code
        in NO_VIG_MARKETS
    ):

        if not no_vig:
            return None

        market_probability = (
            no_vig.get(
                selection_row.selection
            )
        )

        if market_probability is None:
            return None

        probability_method = (
            "NO_VIG"
        )

    # --------------------------------------------------------
    # OVERLAPPING MARKET
    #
    # DC cannot be normalized across 1X / X2 / 12.
    # We use executable-price implied probability.
    # --------------------------------------------------------

    elif (
        market_code
        in OVERLAPPING_MARKETS
    ):

        market_probability = (
            implied_probability_from_odds(
                odds
            )
        )

        probability_method = (
            "DIRECT_IMPLIED"
        )

    else:

        # Unknown market structure.
        #
        # Safer to refuse value calculation
        # than silently use invalid mathematics.

        return None

    edge = (
        float(
            model_probability
        )
        -
        float(
            market_probability
        )
    )

    expected_value = (
        calculate_expected_value(
            model_probability=(
                model_probability
            ),
            odds=odds,
        )
    )

    return {
        "odds":
            odds,

        "market_probability":
            float(
                market_probability
            ),

        "edge":
            float(
                edge
            ),

        "expected_value":
            float(
                expected_value
            ),

        "probability_method":
            probability_method,
    }


# ============================================================
# FIND BEST EXECUTABLE VALUE QUOTE
# ============================================================

def find_best_value_quote(
    db,
    *,
    match_id: int,
    market_code: str,
    selection: str,
    model_probability: float,
    sport: str = "football",
    reference_time=None,
    max_age_hours: int = 12,
):

    market = (
        get_market(
            db=db,
            sport=sport,
            market_code=(
                market_code
            ),
        )
    )

    if market is None:
        return None

    valid_selections = (
        MARKET_SELECTIONS.get(
            market_code
        )
    )

    if (
        not valid_selections
        or selection
        not in valid_selections
    ):
        return None

    # ========================================================
    # FIND BOOKMAKERS THAT OFFER THIS EXACT SELECTION
    # ========================================================

    bookmakers = (
        db.query(
            MarketOdds.bookmaker
        )
        .filter(
            MarketOdds.match_id
            == match_id,

            MarketOdds.market_id
            == market.id,

            MarketOdds.selection
            == selection,
        )
        .distinct()
        .all()
    )

    candidates = []

    # ========================================================
    # EVALUATE EACH BOOKMAKER
    # ========================================================

    for (
        bookmaker,
    ) in bookmakers:

        if not bookmaker:
            continue

        # ----------------------------------------------------
        # DC
        #
        # Only exact selection quote is required.
        # We deliberately DO NOT fetch/normalize all
        # 1X/X2/12 outcomes.
        # ----------------------------------------------------

        if (
            market_code
            in OVERLAPPING_MARKETS
        ):

            selection_row = (
                get_latest_selection_quote(
                    db,
                    match_id=(
                        match_id
                    ),
                    market_id=(
                        market.id
                    ),
                    selection=(
                        selection
                    ),
                    bookmaker=(
                        bookmaker
                    ),
                    reference_time=(
                        reference_time
                    ),
                    max_age_hours=(
                        max_age_hours
                    ),
                )
            )

            if selection_row is None:
                continue

            value = (
                calculate_quote_value(
                    market_code=(
                        market_code
                    ),
                    selection_row=(
                        selection_row
                    ),
                    model_probability=(
                        model_probability
                    ),
                )
            )

            if value is None:
                continue

            candidates.append(
                {
                    "bookmaker":
                        bookmaker,

                    "odds_row":
                        selection_row,

                    "odds":
                        value[
                            "odds"
                        ],

                    "market_probability":
                        value[
                            "market_probability"
                        ],

                    "edge":
                        value[
                            "edge"
                        ],

                    "expected_value":
                        value[
                            "expected_value"
                        ],

                    "probability_method":
                        value[
                            "probability_method"
                        ],

                    "no_vig":
                        None,
                }
            )

            continue

        # ----------------------------------------------------
        # 1X2 / OU25 / BTTS
        #
        # These require the complete bookmaker market so
        # bookmaker margin can be removed.
        # ----------------------------------------------------

        if (
            market_code
            in NO_VIG_MARKETS
        ):

            full_market = (
                get_latest_bookmaker_market(
                    db=db,
                    match_id=(
                        match_id
                    ),
                    market_code=(
                        market_code
                    ),
                    bookmaker=(
                        bookmaker
                    ),
                    sport=(
                        sport
                    ),
                    reference_time=(
                        reference_time
                    ),
                    max_age_hours=(
                        max_age_hours
                    ),
                )
            )

            if not full_market:
                continue

            selection_row = (
                full_market.get(
                    selection
                )
            )

            if selection_row is None:
                continue

            no_vig = (
                calculate_no_vig_probabilities(
                    full_market
                )
            )

            if not no_vig:
                continue

            value = (
                calculate_quote_value(
                    market_code=(
                        market_code
                    ),
                    selection_row=(
                        selection_row
                    ),
                    model_probability=(
                        model_probability
                    ),
                    no_vig=(
                        no_vig
                    ),
                )
            )

            if value is None:
                continue

            candidates.append(
                {
                    "bookmaker":
                        bookmaker,

                    "odds_row":
                        selection_row,

                    "odds":
                        value[
                            "odds"
                        ],

                    "market_probability":
                        value[
                            "market_probability"
                        ],

                    "edge":
                        value[
                            "edge"
                        ],

                    "expected_value":
                        value[
                            "expected_value"
                        ],

                    "probability_method":
                        value[
                            "probability_method"
                        ],

                    "no_vig":
                        no_vig,
                }
            )

    if not candidates:
        return None

    # ========================================================
    # BEST EXECUTABLE PRICE
    # ========================================================

    candidates.sort(
        key=lambda item: (
            item[
                "odds"
            ],
            item[
                "expected_value"
            ],
        ),
        reverse=True,
    )

    return candidates[0]